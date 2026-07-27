"""Synthetic parametric geometry generators.

Constructs building geometries from target parameters (area, aspect ratio,
shape class, storeys) rather than averaging polygon coordinates.

Supported shapes:
- Rectangle
- L-shape
- U-shape
- Courtyard (hollow rectangle)
- T-shape
"""

import math

from shapely.geometry import Polygon


def generate_rectangle(
    area_m2: float,
    aspect_ratio: float = 2.0,
    orientation_deg: float = 0.0,
) -> Polygon:
    """Generate a rectangular footprint from target parameters.

    Parameters
    ----------
    area_m2
        Target footprint area in square metres.
    aspect_ratio
        Length / width ratio (>= 1).
    orientation_deg
        Clockwise rotation from north in degrees.

    Returns
    -------
    Polygon
        Rectangular polygon centred at origin.
    """
    width = math.sqrt(area_m2 / aspect_ratio)
    length = area_m2 / width
    hw, hl = width / 2, length / 2

    coords = [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]

    if orientation_deg != 0:
        angle_rad = math.radians(orientation_deg)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        coords = [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in coords]

    return Polygon(coords)


def generate_l_shape(
    area_m2: float,
    aspect_ratio: float = 2.0,
    wing_fraction: float = 0.5,
    orientation_deg: float = 0.0,
) -> Polygon:
    """Generate an L-shaped footprint.

    Parameters
    ----------
    area_m2
        Target total footprint area.
    aspect_ratio
        Overall bounding box aspect ratio.
    wing_fraction
        Fraction of the bounding box occupied by each wing width (0.3–0.7).
    orientation_deg
        Rotation in degrees.

    Returns
    -------
    Polygon
        L-shaped polygon centred at origin.
    """
    width = math.sqrt(area_m2 / aspect_ratio)
    length = area_m2 / width
    wf = max(0.3, min(0.7, wing_fraction))
    wing_w = width * wf

    # L-shape: main bar along length + perpendicular wing
    # Adjust to hit target area
    # Area = length * wing_w + (width - wing_w) * wing_w
    # Solve for actual dimensions to match target
    actual_area = length * wing_w + (width - wing_w) * wing_w
    scale = math.sqrt(area_m2 / actual_area) if actual_area > 0 else 1.0
    length *= scale
    width *= scale
    wing_w *= scale

    # Build L from bottom-left
    x0, y0 = -length / 2, -width / 2
    coords = [
        (x0, y0),
        (x0 + length, y0),
        (x0 + length, y0 + wing_w),
        (x0 + wing_w, y0 + wing_w),
        (x0 + wing_w, y0 + width),
        (x0, y0 + width),
    ]

    if orientation_deg != 0:
        angle_rad = math.radians(orientation_deg)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        coords = [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in coords]

    return Polygon(coords)


def generate_u_shape(
    area_m2: float,
    aspect_ratio: float = 1.5,
    wing_depth_fraction: float = 0.6,
    wing_width_fraction: float = 0.3,
    orientation_deg: float = 0.0,
) -> Polygon:
    """Generate a U-shaped footprint.

    Parameters
    ----------
    area_m2
        Target total footprint area.
    aspect_ratio
        Overall bounding box aspect ratio.
    wing_depth_fraction
        How deep the wings extend (fraction of total length).
    wing_width_fraction
        Width of each wing as fraction of total width.
    orientation_deg
        Rotation in degrees.

    Returns
    -------
    Polygon
        U-shaped polygon centred at origin.
    """
    # Start with bounding box
    width = math.sqrt(area_m2 / aspect_ratio) * 1.3  # oversized, then scale
    length = width * aspect_ratio
    ww = width * wing_width_fraction
    wd = length * wing_depth_fraction
    base_depth = length - wd

    # U-shape area = base_bar + 2 wings
    # base_bar = width * base_depth
    # each wing = ww * wd
    actual_area = width * base_depth + 2 * ww * wd
    scale = math.sqrt(area_m2 / actual_area) if actual_area > 0 else 1.0
    width *= scale
    length *= scale
    ww *= scale
    wd *= scale
    base_depth *= scale

    x0, y0 = -width / 2, -length / 2
    coords = [
        (x0, y0),
        (x0 + width, y0),
        (x0 + width, y0 + wd + base_depth),  # right wing top
        (x0 + width - ww, y0 + wd + base_depth),
        (x0 + width - ww, y0 + base_depth),
        (x0 + ww, y0 + base_depth),
        (x0 + ww, y0 + wd + base_depth),  # left wing top
        (x0, y0 + wd + base_depth),
    ]

    if orientation_deg != 0:
        angle_rad = math.radians(orientation_deg)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        coords = [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in coords]

    return Polygon(coords)


def generate_courtyard(
    area_m2: float,
    aspect_ratio: float = 1.2,
    courtyard_fraction: float = 0.25,
    orientation_deg: float = 0.0,
) -> Polygon:
    """Generate a courtyard (hollow rectangle) footprint.

    Parameters
    ----------
    area_m2
        Target footprint area (excluding courtyard void).
    aspect_ratio
        Outer rectangle aspect ratio.
    courtyard_fraction
        Fraction of outer area that is the courtyard void.
    orientation_deg
        Rotation in degrees.

    Returns
    -------
    Polygon
        Rectangle with interior hole (courtyard).
    """
    # outer_area = area_m2 + courtyard_area
    # courtyard_area = courtyard_fraction * outer_area
    # => outer_area = area_m2 / (1 - courtyard_fraction)
    outer_area = area_m2 / (1.0 - courtyard_fraction)
    outer_width = math.sqrt(outer_area / aspect_ratio)
    outer_length = outer_area / outer_width

    # Courtyard is centred, scaled version
    court_scale = math.sqrt(courtyard_fraction)
    court_w = outer_width * court_scale
    court_l = outer_length * court_scale

    hw, hl = outer_width / 2, outer_length / 2
    chw, chl = court_w / 2, court_l / 2

    exterior = [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]
    interior = [(-chl, -chw), (-chl, chw), (chl, chw), (chl, -chw)]

    if orientation_deg != 0:
        angle_rad = math.radians(orientation_deg)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        exterior = [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in exterior]
        interior = [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in interior]

    return Polygon(exterior, [interior])


def generate_t_shape(
    area_m2: float,
    aspect_ratio: float = 1.8,
    stem_fraction: float = 0.4,
    orientation_deg: float = 0.0,
) -> Polygon:
    """Generate a T-shaped footprint.

    Parameters
    ----------
    area_m2
        Target total footprint area.
    aspect_ratio
        Overall bounding box aspect ratio.
    stem_fraction
        Width of the stem as fraction of total width.
    orientation_deg
        Rotation in degrees.

    Returns
    -------
    Polygon
        T-shaped polygon centred at origin.
    """
    width = math.sqrt(area_m2 / aspect_ratio)
    length = width * aspect_ratio
    stem_w = width * stem_fraction
    bar_h = length * 0.35  # top bar height

    # T: top bar (full width) + stem
    stem_h = length - bar_h
    actual_area = width * bar_h + stem_w * stem_h
    scale = math.sqrt(area_m2 / actual_area) if actual_area > 0 else 1.0
    width *= scale
    length *= scale
    stem_w *= scale
    bar_h *= scale
    stem_h *= scale

    x0, y0 = -width / 2, -length / 2
    stem_x = (width - stem_w) / 2
    coords = [
        (x0 + stem_x, y0),
        (x0 + stem_x + stem_w, y0),
        (x0 + stem_x + stem_w, y0 + stem_h),
        (x0 + width, y0 + stem_h),
        (x0 + width, y0 + length),
        (x0, y0 + length),
        (x0, y0 + stem_h),
        (x0 + stem_x, y0 + stem_h),
    ]

    if orientation_deg != 0:
        angle_rad = math.radians(orientation_deg)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
        coords = [(x * cos_a - y * sin_a, x * sin_a + y * cos_a) for x, y in coords]

    return Polygon(coords)
