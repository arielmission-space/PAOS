import numpy as np
from paos import logger
from skimage.transform import rescale, resize
from scipy.ndimage import fourier_shift


def resample_grid_sag(
    sag: np.ndarray,
    nx: int,
    ny: int,
    nx_new: int,
    ny_new: int,
    delx: float,
    dely: float,
    delx_new: float,
    dely_new: float,
    xdec: float = 0.0,
    ydec: float = 0.0,
    order: int = 1,
    mask_tol: float = 0.001,
):
    """
    Resample a 2D sag map onto a new regularly spaced grid.

    The input sag is converted to a masked array (masking non-finite and zero
    values), optionally shifted by sub-pixel offsets using Fourier-domain
    shifting, then padded/cropped to match the target physical extent, and
    finally rescaled/resized to (ny_new, nx_new) with the requested pixel
    spacings.

    Parameters
    ----------
    sag : ndarray
        2D sag map of shape (ny, nx). Non-finite values and zeros are treated
        as invalid and masked (unless `sag` is already a MaskedArray).
    nx, ny : int
        Input grid size in pixels (x and y).
    nx_new, ny_new : int
        Output grid size in pixels (x and y).
    delx, dely : float
        Input pixel spacing along x and y (same units as `delx_new`, `dely_new`).
    delx_new, dely_new : float
        Desired output pixel spacing along x and y.
    xdec, ydec : float, optional
        Sub-pixel shift (in pixels) applied before resampling (Fourier shift).
    order : int, optional
        Interpolation order passed to scikit-image resampling routines.
    mask_tol : float, optional
        Threshold applied to the resampled mask; values above this are masked.

    Returns
    -------
    numpy.ma.MaskedArray
        Resampled sag map of shape (ny_new, nx_new) with an updated mask.

    Raises
    ------
    AssertionError
        If `sag` is not 2D or does not match shape (ny, nx).
    """

    shape_new = (ny_new, nx_new)

    def rescale_map(sag, mask, scale_x, scale_y):
        anti_aliasing = (
            scale_x < 1.0 or scale_y < 1.0
        )  # anti_aliasing is required for downsampling

        sag = rescale(
            sag,
            scale=(scale_y, scale_x),
            anti_aliasing=anti_aliasing,
            order=order,
        )

        mask = rescale(
            mask,
            scale=(scale_y, scale_x),
            anti_aliasing=anti_aliasing,
            order=order,
        )

        return sag, mask

    def pad_map(sag, mask, padding):
        sag = np.pad(
            sag,
            padding,
            mode="constant",
            constant_values=0,
        )
        mask = np.pad(
            mask,
            padding,
            mode="constant",
            constant_values=1,
        )
        return sag, mask

    def resize_map(sag, mask, scale_x, scale_y):
        anti_aliasing = (
            scale_x < 1.0 or scale_y < 1.0
        )  # anti_aliasing is required for downsampling

        sag = resize(
            sag,
            output_shape=shape_new,
            anti_aliasing=anti_aliasing,
            order=order,
        )
        mask = resize(
            mask,
            output_shape=shape_new,
            anti_aliasing=anti_aliasing,
            order=order,
        )
        return sag, mask

    assert sag.ndim == 2, "sag shall be a 2D array"
    assert sag.shape == (ny, nx)

    logger.debug("Converting sag to masked array")
    if isinstance(sag, np.ma.MaskedArray):
        logger.debug("Input sag is already a masked array")
    else:
        logger.debug("Input sag is not a masked array")
        mask = ~np.isfinite(sag) | (sag == 0)
        sag = np.ma.MaskedArray(sag, mask=mask)

    mask = sag.mask.astype(float)
    sag = sag.filled(0.0)

    # Step 1: recenter
    if (xdec != 0) or (ydec != 0):
        logger.debug("Applying sag shift: xdec = %f, ydec = %f" % (xdec, ydec))
        sag = fourier_shift(np.fft.fft2(sag), shift=(-xdec, -ydec))
        sag = np.fft.ifft2(sag).real
        mask = fourier_shift(np.fft.fft2(mask), shift=(-xdec, -ydec))
        mask = np.fft.ifft2(mask).real

    # Step 2: pad or crop
    target_width = shape_new[1] * delx_new
    target_height = shape_new[0] * dely_new

    current_width = sag.shape[1] * delx
    current_height = sag.shape[0] * dely

    logger.debug(
        f"target width [m]: {target_width}, target height [m]: {target_height}"
    )
    logger.debug(
        f"current width [m]: {current_width}, current height [m]: {current_height}"
    )

    width_diff = int(np.floor((current_width - target_width) / delx))
    height_diff = int(np.floor((current_height - target_height) / dely))

    scale_x = scale_y = 1
    if width_diff % 2 == 1 or height_diff % 2 == 1:
        logger.debug(f"I need to sample more finely. Sag shape is {sag.shape}")

    if width_diff % 2 == 1:
        scale_x = 2
        delx /= 2
        width_diff *= 2

    if height_diff % 2 == 1:
        scale_y = 2
        dely /= 2
        height_diff *= 2

    if (scale_x != 1) or (scale_y != 1):
        sag, mask = rescale_map(sag, mask, scale_x, scale_y)
    logger.debug(f"Resampled sag shape is {sag.shape}")

    # Handle width dimension (x-axis)
    if width_diff < 0.0:
        logger.debug("Applying padding on width...")
        pad_width = abs(width_diff)
        pad_left = pad_width // 2
        pad_right = pad_width - pad_left
        sag, mask = pad_map(sag, mask, ((0, 0), (pad_left, pad_right)))

    elif width_diff > 0.0:
        logger.debug("Applying cropping on width...")
        crop_width = width_diff
        crop_left = crop_width // 2
        crop_right = sag.shape[1] - (crop_width - crop_left)

        # Apply cropping only on x-axis
        sag = sag[:, crop_left:crop_right]
        mask = mask[:, crop_left:crop_right]

    # Handle height dimension (y-axis)
    if height_diff < 0.0:
        logger.debug("Applying padding on height...")
        pad_height = abs(height_diff)
        pad_top = pad_height // 2
        pad_bottom = pad_height - pad_top
        sag, mask = pad_map(sag, mask, ((pad_top, pad_bottom), (0, 0)))

    elif height_diff > 0.0:
        logger.debug("Applying cropping on height...")
        crop_height = height_diff
        crop_top = crop_height // 2
        crop_bottom = sag.shape[0] - (crop_height - crop_top)

        # Apply cropping only on y-axis
        sag = sag[crop_top:crop_bottom, :]
        mask = mask[crop_top:crop_bottom, :]
    logger.debug(f"Adjusted sag shape is {sag.shape}, mask shape is {mask.shape}")

    # Step 3: rescale
    scale_x = delx / delx_new
    scale_y = dely / dely_new

    if (scale_x != 1) or (scale_y != 1):
        sag, mask = rescale_map(sag, mask, scale_x, scale_y)

    # Step 4: resize
    # if the shape is not the same as the input (could be 1 pixel off), resize
    logger.debug(f"Resampled sag shape is {sag.shape}")

    if sag.shape != shape_new:
        logger.debug(f"Output shape should be {shape_new}: resizing...")
        scale_x = shape_new[1] / sag.shape[1]
        scale_y = shape_new[0] / sag.shape[0]
        sag, mask = resize_map(sag, mask, scale_x, scale_y)

    mask = mask > mask_tol
    sag = np.ma.MaskedArray(sag, mask=mask)

    return sag
