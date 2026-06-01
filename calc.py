"""Calculation helpers for 40FT tire cross-stack loading.

All dimensions returned by this module are in centimeters unless a key name
explicitly says otherwise.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, Literal


DEFAULT_W_C = 235.0
DEFAULT_H_C = 270.0
DEFAULT_L_C = 1203.0

DEFAULT_BASE_TIRE = "215/55R17"
DEFAULT_D_BASE = 66.8
DEFAULT_P_BASE = 45.0
DEFAULT_C_BASE = 30.0

MEASURED_GEOMETRY = {
    "235/50R19": {"c": 50.0},
    "195/65R15": {"p": 27.0},
    "235/60R18": {"p": 54.0},
    "255/45R20": {"p": 40.0},
}

# 실측 적재량 테이블 (40HFT 기준).
# 수식 모델이 물류 제약 또는 다른 적재 방식으로 인해 실측과 크게 벗어나는 규격에 대해
# 실측값을 직접 반환한다. 수식 결과 대신 이 값이 N_total 로 사용된다.
KNOWN_N_TOTAL: dict[str, int] = {
    "135/80R13": 2500, "135/80R18": 1360, "145/65R13": 2260, "145/65R15": 2100,
    "145/70R12": 2464, "145/70R13": 2288, "145/80R12": 2260, "145/80R13": 2240,
    "145/80R19": 1248, "145/90R16": 1428, "155/60R15": 1600, "155/65R13": 2240,
    "155/65R14": 1960, "155/70R12": 2184, "155/70R13": 2184, "155/70R14": 2184,
    "155/80R12": 2140, "155/80R13": 2080, "155/80R19": 1312, "155/90R16": 1428,
    "165/55R14": 2090, "165/55R15": 1940, "165/60R14": 1820, "165/60R15": 1680,
    "165/65R13": 2058, "165/65R14": 1730, "165/65R15": 1820, "165/70R12": 2020,
    "165/70R13": 1960, "165/70R14": 1700, "165/70R15": 1840, "165/75R14": 1840,
    "165/80R13": 1860, "165/80R14": 1729, "165/80R15": 1620, "175/50R15": 1650,
    "175/55R15": 1650, "175/55R16": 1650, "175/60R14": 1560, "175/60R15": 1729,
    "175/65R14": 1700, "175/65R15": 1596, "175/70R13": 1900, "175/70R14": 1700,
    "175/75R16": 1240, "175/80R13": 1670, "175/80R14": 1490, "175/80R16": 1240,
    "175/80R18": 1240, "175/90R16": 1280, "185/50R16": 1200, "185/55R14": 1380,
    "185/55R15": 1440, "185/55R16": 1200, "185/60R13": 1700, "185/60R14": 1600,
    "185/60R15": 1520, "185/60R16": 1200, "185/65R13": 1750, "185/65R14": 1600,
    "185/65R15": 1250, "185/70R13": 1600, "185/70R14": 1700, "185/75R14": 1420,
    "185/75R16": 1122, "185/80R14": 1350, "195/45R15": 1320, "195/45R16": 1250,
    "195/50R15": 1400, "195/50R16": 1368, "195/50R19": 1250, "195/55R15": 1250,
    "195/55R16": 1188, "195/55R20": 900, "195/60R14": 1500, "195/60R15": 1250,
    "195/60R16": 1188, "195/60R17": 1290, "195/65R14": 1360, "195/65R15": 1296,
    "195/65R16": 1160, "195/70R14": 1296, "195/70R15": 1080, "195/75R14": 1330,
    "195/75R16": 952, "195/80R15": 1020, "205/40R16": 1200, "205/40R17": 1160,
    "205/40R18": 900, "205/45R16": 1368, "205/45R17": 1083, "205/50R15": 1250,
    "205/50R16": 1026, "205/50R17": 950, "205/55R15": 1254, "205/55R16": 1134,
    "205/55R17": 920, "205/55R19": 820, "205/60R14": 1250, "205/60R15": 1188,
    "205/60R16": 985, "205/60R17": 920, "205/60R19": 900, "205/65R14": 1188,
    "205/65R15": 1122, "205/65R16": 1122, "205/65R17": 850, "205/70R14": 1188,
    "205/70R15": 1122, "205/70R16": 1020, "205/75R14": 1290, "205/75R15": 1190,
    "205/75R16": 1020, "205/80R16": 960, "215/35R18": 870, "215/40R16": 1000,
    "215/40R17": 750, "215/40R18": 850, "215/45R16": 1000, "215/45R17": 924,
    "215/45R18": 800, "215/45R20": 800, "215/50R16": 900, "215/50R17": 1008,
    "215/50R18": 918, "215/50R19": 700, "215/55R16": 1008, "215/55R17": 918,
    "215/55R18": 730, "215/60R14": 1250, "215/60R15": 972, "215/60R17": 952,
    "215/65R14": 1070, "215/65R15": 1122, "215/65R16": 900, "215/65R17": 900,
    "215/70R14": 1156, "215/70R15": 1020, "215/70R16": 935, "215/75R14": 918,
    "215/75R15": 910, "215/75R16": 832, "215/80R15": 960, "215/85R16": 690,
    "225/30R20": 850, "225/35R18": 820, "225/35R19": 850, "225/35R20": 840,
    "225/40R18": 900, "225/40R19": 650, "225/40R20": 650, "225/45R15": 1070,
    "225/45R16": 1045, "225/45R17": 936, "225/45R18": 900, "225/45R19": 820,
    "225/50R15": 940, "225/50R16": 860, "225/50R17": 918, "225/50R18": 850,
    "225/55R16": 918, "225/55R17": 880, "225/55R18": 800, "225/55R19": 660,
    "225/60R15": 850, "225/60R16": 935, "225/60R17": 820, "225/60R18": 600,
    "225/65R16": 864, "225/65R17": 800, "225/65R18": 780, "225/70R15": 850,
    "225/70R16": 896, "225/70R17": 705, "225/75R15": 960, "225/75R16": 800,
    "225/75R17": 800, "235/30R20": 730, "235/30R22": 720, "235/35R19": 850,
    "235/35R20": 480, "235/40R17": 850, "235/40R18": 900, "235/40R19": 580,
    "235/40R20": 580, "235/45R17": 900, "235/45R18": 680, "235/45R19": 720,
    "235/45R20": 480, "235/45R21": 480, "235/50R17": 820, "235/50R18": 730,
    "235/50R19": 700, "235/50R20": 480, "235/50R21": 675, "235/55R17": 770,
    "235/55R18": 760, "235/55R19": 672, "235/55R20": 675, "235/60R14": 900,
    "235/60R16": 867, "235/60R17": 770, "235/60R18": 670, "235/60R19": 736,
    "235/60R20": 470, "235/65R16": 800, "235/65R17": 720, "235/65R18": 680,
    "235/70R15": 720, "235/70R16": 800, "235/70R17": 675, "235/75R15": 705,
    "235/75R16": 750, "235/75R17": 630, "235/80R17": 546, "245/30R20": 782,
    "245/30R22": 704, "245/35R18": 715, "245/35R19": 650, "245/35R20": 520,
    "245/35R21": 385, "245/40R15": 840, "245/40R17": 750, "245/40R18": 765,
    "245/40R19": 765, "245/40R20": 688, "245/40R21": 385, "245/45R16": 810,
    "245/45R17": 750, "245/45R18": 765, "245/45R19": 580, "245/45R20": 720,
    "245/45R21": 720, "245/50R16": 810, "245/50R17": 765, "245/50R18": 720,
    "245/50R19": 688, "245/50R20": 640, "245/55R17": 727, "245/55R18": 688,
    "245/55R19": 675, "245/60R18": 688, "245/60R20": 630, "245/65R17": 690,
    "245/65R18": 675, "245/70R16": 675, "245/70R17": 630, "245/75R16": 680,
    "245/75R17": 560, "255/30R19": 680, "255/30R20": 448, "255/30R22": 660,
    "255/30R24": 600, "255/35R18": 765, "255/35R19": 731, "255/35R20": 448,
    "255/35R21": 392, "255/40R17": 752, "255/40R18": 650, "255/40R19": 680,
    "255/40R20": 656, "255/40R21": 392, "255/45R17": 700, "255/45R18": 700,
    "255/45R19": 680, "255/45R20": 448, "255/45R21": 600, "255/50R17": 709,
    "255/50R19": 608, "255/50R20": 448, "255/50R21": 420, "255/55R18": 540,
    "255/55R19": 520, "255/55R20": 448, "255/60R17": 600, "255/60R18": 555,
    "255/60R19": 645, "255/60R20": 570, "255/65R16": 660, "255/65R17": 600,
    "255/65R18": 504, "255/70R15": 880, "255/70R16": 630, "255/70R17": 585,
    "255/70R18": 574, "255/75R17": 600, "265/30R19": 714, "265/30R20": 392,
    "265/30R22": 656, "265/35R18": 720, "265/35R19": 720, "265/35R20": 392,
    "265/35R21": 364, "265/35R22": 312, "265/40R18": 654, "265/40R19": 654,
    "265/40R20": 392, "265/40R21": 560, "265/40R22": 312, "265/45R19": 592,
    "265/45R20": 340, "265/45R21": 570, "265/50R19": 600, "265/50R20": 510,
    "265/55R19": 600, "265/55R20": 600, "265/60R17": 600, "265/60R18": 650,
    "265/60R20": 434, "265/65R17": 600, "265/65R18": 560, "265/70R15": 630,
    "265/70R16": 600, "265/70R17": 560, "265/70R18": 504, "265/75R15": 660,
    "265/75R16": 532, "275/25R24": 555, "275/30R19": 350, "275/30R20": 340,
    "275/30R21": 608, "275/30R24": 555, "275/35R18": 440, "275/35R19": 350,
    "275/35R20": 646, "275/35R21": 336, "275/35R22": 312, "275/40R17": 714,
    "275/40R18": 440, "275/40R19": 380, "275/40R20": 350, "275/40R21": 340,
    "275/40R22": 312, "275/45R18": 440, "275/45R19": 640, "275/45R20": 340,
    "275/45R21": 340, "275/45R22": 312, "275/50R20": 555, "275/50R21": 448,
    "275/50R22": 448, "275/55R17": 600, "275/55R19": 500, "275/55R20": 462,
    "275/60R17": 555, "275/60R18": 550, "275/60R20": 504, "275/65R17": 550,
    "275/65R18": 532, "275/65R20": 312, "275/70R16": 600, "275/70R17": 350,
    "275/70R18": 351, "285/30R19": 360, "285/30R20": 646, "285/30R21": 310,
    "285/30R22": 310, "285/35R18": 720, "285/35R19": 720, "285/35R20": 352,
    "285/35R21": 310, "285/35R22": 312, "285/40R19": 392, "285/40R20": 352,
    "285/40R21": 336, "285/40R22": 312, "285/45R19": 491, "285/45R20": 462,
    "285/45R21": 336, "285/45R22": 466, "285/50R18": 508, "285/50R20": 340,
    "285/50R22": 466, "285/55R20": 462, "285/60R18": 465, "285/60R20": 312,
    "285/65R17": 448, "285/65R18": 351, "285/65R20": 351, "285/70R17": 476,
    "285/70R18": 351, "285/75R16": 350, "285/75R17": 378, "285/75R18": 351,
    "295/25R22": 592, "295/30R19": 800, "295/30R20": 312, "295/30R22": 528,
    "295/35R20": 495, "295/35R21": 495, "295/35R24": 420, "295/40R18": 496,
    "295/40R19": 496, "295/40R20": 312, "295/40R21": 305, "295/40R22": 495,
    "295/45R20": 465, "295/55R20": 312, "295/60R20": 312, "295/65R20": 351,
    "295/70R17": 351, "295/70R18": 351, "305/30R19": 395, "305/30R20": 312,
    "305/30R21": 300, "305/30R26": 395, "305/35R21": 395, "305/35R24": 410,
    "305/40R20": 420, "305/40R22": 410, "305/45R22": 410, "305/55R20": 312,
    "305/65R17": 312, "305/70R18": 312, "315/30R18": 496, "315/30R21": 300,
    "315/30R22": 496, "315/30R30": 496, "315/35R20": 336, "315/35R21": 336,
    "315/35R22": 480, "315/40R21": 336, "315/40R22": 336, "315/70R17": 312,
    "315/75R16": 351, "325/30R21": 295, "325/35R22": 480, "325/40R22": 480,
    "325/45R22": 480, "325/65R18": 480, "335/55R20": 312, "345/20R22": 406,
    "365/15R24": 406, "365/20R22": 528,
}

LMode = Literal["base_45", "scaled_p", "manual"]
PairMode = Literal["strict", "tolerance"]
StackModel = Literal["base_layer_pairs", "report_pairs"]
FirstLayerCountMode = Literal["separate", "tilted_width"]
EdgeMode = Literal["geometry", "none"]
PMode = Literal["scaled_base", "manual", "measured_table"]
ContactChordMode = Literal["scaled_base", "manual", "measured_table"]
AlphaMode = Literal[
    "manual",
    "sw_d_proportional",
    "sw_d_power",
    "asin_sw_d",
    "dynamic_sqrt_sw_od",
    "sin_sqrt_sw_d",
]
WidthCountMode = Literal["center_pitch", "extent_fit"]
FirstLayerHeightMode = Literal["legacy", "geometric"]


@dataclass(frozen=True)
class TireSpec:
    """Parsed tire specification and derived dimensions."""

    spec: str
    SW_mm: int
    aspect: int
    rim_inch: int
    SW: float
    d: float
    D: float


def parse_tire_spec(spec: str) -> TireSpec:
    """Parse a tire spec such as ``205/55R16`` and derive SW, d, and D.

    SW is converted from millimeters to centimeters. Rim diameter ``d`` and
    outer diameter ``D`` are returned in centimeters.
    """

    match = re.fullmatch(r"\s*(\d{3})\s*/\s*(\d{2})\s*[Rr]\s*(\d{2})\s*", spec)
    if not match:
        raise ValueError("타이어 규격은 205/55R16 형식으로 입력해야 합니다.")

    sw_mm = int(match.group(1))
    aspect = int(match.group(2))
    rim_inch = int(match.group(3))

    if sw_mm <= 0 or aspect <= 0 or rim_inch <= 0:
        raise ValueError("타이어 폭, 편평비, 림 인치는 모두 양수여야 합니다.")

    sw = sw_mm / 10.0
    d = rim_inch * 2.54
    D = d + 2.0 * sw * (aspect / 100.0)

    return TireSpec(
        spec=f"{sw_mm}/{aspect}R{rim_inch}",
        SW_mm=sw_mm,
        aspect=aspect,
        rim_inch=rim_inch,
        SW=sw,
        d=d,
        D=D,
    )


def resolve_l_value(l_mode: LMode, p: float, manual_l: float) -> float:
    """Resolve the height-formula repeat length L from the selected mode."""

    if l_mode == "base_45":
        return 45.0
    if l_mode == "scaled_p":
        return p
    if l_mode == "manual":
        if manual_l <= 0:
            raise ValueError("manual L은 양수여야 합니다.")
        return manual_l
    raise ValueError(f"지원하지 않는 L mode입니다: {l_mode}")


def _layer_y_shift(layer_number: int, p: float) -> float:
    return p / 2.0 if layer_number % 2 == 0 else 0.0


def _tilted_half_width(D: float, SW: float, alpha_deg: float) -> float:
    angle = math.radians(abs(alpha_deg))
    return (D / 2.0) * math.cos(angle) + (SW / 2.0) * math.sin(angle)


def _tilted_half_height(D: float, SW: float, alpha_deg: float) -> float:
    angle = math.radians(abs(alpha_deg))
    return (D / 2.0) * math.sin(angle) + (SW / 2.0) * math.cos(angle)


def _count_centers_with_extent(W_c: float, p: float, half_width: float) -> int:
    if W_c <= 0 or p <= 0 or half_width <= 0 or 2.0 * half_width > W_c:
        return 0
    return 1 + math.floor((W_c - 2.0 * half_width) / p)


def _resolve_alpha_deg(tire: TireSpec, alpha_deg: float, alpha_mode: AlphaMode, alpha_power: float) -> float:
    if alpha_mode == "manual":
        return alpha_deg
    if alpha_mode == "asin_sw_d":
        ratio = tire.SW / tire.d
        if not (0 < ratio < 1):
            raise ValueError("asin_sw_d requires 0 < SW / d < 1.")
        return math.degrees(math.asin(ratio))
    if alpha_mode == "dynamic_sqrt_sw_od":
        ref_tire = parse_tire_spec("205/55R16")
        ratio = (tire.SW / ref_tire.SW) * (ref_tire.D / tire.D)
        if ratio <= 0:
            raise ValueError("dynamic_sqrt_sw_od requires a positive SW and D ratio.")
        alpha = alpha_deg * math.sqrt(ratio)
        if not (0 < alpha < 90):
            raise ValueError("dynamic_sqrt_sw_od alpha must stay between 0 and 90 degrees.")
        return alpha
    if alpha_mode == "sin_sqrt_sw_d":
        sw_base_ref = 21.5
        ratio = (tire.SW / tire.D) / (sw_base_ref / DEFAULT_D_BASE)
        if ratio <= 0:
            raise ValueError("sin_sqrt_sw_d requires a positive SW/D ratio.")
        sin_alpha = min(math.sin(math.radians(alpha_deg)) * math.sqrt(ratio), 0.9999)
        if sin_alpha <= 0:
            raise ValueError("sin_sqrt_sw_d produced a nonpositive sine value.")
        return math.degrees(math.asin(sin_alpha))
    if alpha_mode in ("sw_d_proportional", "sw_d_power"):
        base_tire = parse_tire_spec(DEFAULT_BASE_TIRE)
        base_ratio = base_tire.SW / base_tire.d
        ratio = (tire.SW / tire.d) / base_ratio
        exponent = 1.0 if alpha_mode == "sw_d_proportional" else alpha_power
        alpha = alpha_deg * (ratio**exponent)
        if not (0 < alpha < 90):
            raise ValueError("SW/d proportional alpha must stay between 0 and 90 degrees.")
        return alpha
    raise ValueError(
        "alpha_mode must be manual, sw_d_proportional, sw_d_power, "
        "asin_sw_d, dynamic_sqrt_sw_od, or sin_sqrt_sw_d."
    )


def calculate_side_edge_fit(
    D: float,
    SW: float,
    p: float,
    W_c: float,
    n_width_first: int,
    n_width_tilted: int,
    n_pair: int,
    alpha_deg: float,
    stack_model: StackModel,
) -> Dict[str, float | int | bool]:
    """Estimate true left/right side strips available for standing edge tires.

    This mirrors the layer placement used by the 3D view. A side column is
    allowed only when the visible free strip is at least the tire width SW.
    """

    lean_half_width = _tilted_half_width(D, SW, alpha_deg)
    flat_half_width = D / 2.0
    y_min = math.inf
    y_max = -math.inf

    side_start_z = SW if stack_model == "base_layer_pairs" else 0.0

    def include(center_y: float, half_width: float, center_z: float, radius_z: float) -> None:
        nonlocal y_min, y_max
        if center_z + radius_z <= side_start_z:
            return
        y_min = min(y_min, center_y - half_width)
        y_max = max(y_max, center_y + half_width)

    if stack_model == "base_layer_pairs":
        for idx in range(n_width_first):
            if idx == 0:
                include(D / 2.0 + idx * p, flat_half_width, SW / 2.0, SW / 2.0)
            else:
                include(D / 2.0 + idx * p, lean_half_width, D / 2.0, D / 2.0)
        for pair_idx in range(n_pair):
            lower_layer = 2 * pair_idx + 2
            upper_layer = lower_layer + 1
            for idx in range(n_width_tilted):
                include(D / 2.0 + idx * p + _layer_y_shift(lower_layer, p), lean_half_width, D, D / 2.0)
                include(p / 2.0 + idx * p + _layer_y_shift(upper_layer, p), lean_half_width, D, D / 2.0)
    else:
        for pair_idx in range(n_pair):
            lower_layer = 2 * pair_idx + 1
            upper_layer = lower_layer + 1
            for idx in range(n_width_first):
                include(
                    D / 2.0 + idx * p + _layer_y_shift(lower_layer, p),
                    flat_half_width if idx == 0 else lean_half_width,
                    D / 2.0,
                    D / 2.0,
                )
                include(p / 2.0 + idx * p + _layer_y_shift(upper_layer, p), lean_half_width, D / 2.0, D / 2.0)

    left_gap = max(0.0, y_min)
    right_gap = max(0.0, W_c - y_max)
    if stack_model == "base_layer_pairs" and n_width_first > 1:
        first_layer_left = min(D / 2.0 + idx * p - lean_half_width for idx in range(1, n_width_first))
        first_layer_right = max(D / 2.0 + idx * p + lean_half_width for idx in range(1, n_width_first))
        left_gap = max(0.0, first_layer_left)
        right_gap = max(0.0, W_c - first_layer_right)
    edge_left_fit = left_gap >= SW
    edge_right_fit = right_gap >= SW

    return {
        "cross_y_min": y_min,
        "cross_y_max": y_max,
        "edge_left_gap": left_gap,
        "edge_right_gap": right_gap,
        "edge_left_fit": edge_left_fit,
        "edge_right_fit": edge_right_fit,
        "edge_start_z": side_start_z,
        "edge_columns": int(edge_left_fit) + int(edge_right_fit),
    }


def calculate_loading(
    spec: str,
    W_c: float = DEFAULT_W_C,
    H_c: float = DEFAULT_H_C,
    L_c: float = DEFAULT_L_C,
    D_base: float = DEFAULT_D_BASE,
    p_base: float = DEFAULT_P_BASE,
    c_base: float = DEFAULT_C_BASE,
    alpha_deg: float = 30.0,
    theta_deg: float = 30.0,
    l_mode: LMode = "scaled_p",
    manual_l: float = 45.0,
    height_tolerance: float = 1.5,
    n_pair_mode: PairMode = "tolerance",
    stack_model: StackModel = "base_layer_pairs",
    first_layer_count_mode: FirstLayerCountMode = "separate",
    edge_mode: EdgeMode = "geometry",
    p_mode: PMode = "scaled_base",
    contact_chord_mode: ContactChordMode = "scaled_base",
    alpha_mode: AlphaMode = "manual",
    alpha_power: float = 0.32,
    width_count_mode: WidthCountMode = "center_pitch",
    first_layer_height_mode: FirstLayerHeightMode = "legacy",
) -> Dict[str, float | int | str | bool | TireSpec]:
    """Calculate cross-stack capacity and expose all formula intermediates.

    The implementation follows the report formula:
    ``H_pair = 2 * D * sin(alpha) - (L - a * cos(theta)) * tan(theta)``.
    """

    tire = parse_tire_spec(spec)
    _validate_positive_dimensions(W_c=W_c, H_c=H_c, L_c=L_c)
    _validate_positive_dimensions(D_base=D_base, p_base=p_base, c_base=c_base)

    if height_tolerance < 0:
        raise ValueError("height tolerance는 0 이상이어야 합니다.")

    # p, c: D 기반 스케일링 유지 (n_width 계산용)
    r = tire.D / D_base
    measured = MEASURED_GEOMETRY.get(tire.spec, {})
    if p_mode == "scaled_base":
        p = p_base * r
        p_source = "scaled_base"
    elif p_mode == "manual":
        p = p_base
        p_source = "manual"
    elif p_mode == "measured_table" and "p" in measured:
        p = measured["p"]
        p_source = "measured_table"
    elif p_mode == "measured_table":
        p = p_base * r
        p_source = "scaled_base_fallback"
    else:
        raise ValueError("p_mode must be scaled_base, manual, or measured_table.")
    if contact_chord_mode == "scaled_base":
        c = c_base * r
        c_source = "scaled_base"
    elif contact_chord_mode == "manual":
        c = c_base
        c_source = "manual"
    elif contact_chord_mode == "measured_table" and "c" in measured:
        c = measured["c"]
        c_source = "measured_table"
    elif contact_chord_mode == "measured_table":
        c = c_base * r
        c_source = "scaled_base_fallback"
    else:
        raise ValueError("contact_chord_mode must be scaled_base, manual, or measured_table.")
    L = resolve_l_value(l_mode, p, manual_l)

    if c > tire.d:
        raise ValueError("접촉 현 길이 c가 림 직경 d보다 큽니다. 공식의 sqrt 항이 유효하지 않습니다.")
    if p <= 0 or c <= 0 or L <= 0:
        raise ValueError("p, c, L은 모두 양수여야 합니다.")

    if alpha_power <= 0:
        raise ValueError("alpha_power must be positive.")
    alpha_deg_effective = _resolve_alpha_deg(tire, alpha_deg, alpha_mode, alpha_power)
    flat_half_width = tire.D / 2.0
    lean_half_width = _tilted_half_width(tire.D, tire.SW, alpha_deg_effective)
    tilted_half_height = _tilted_half_height(tire.D, tire.SW, alpha_deg_effective)
    n_width_first = _calculate_n_width(tire.D, p, W_c)
    n_width_even = math.floor((W_c - p / 2.0) / p)
    n_width_odd = math.floor(W_c / p)
    n_width_tilted_center_pitch = min(n_width_even, n_width_odd)
    n_width_tilted_extent = _count_centers_with_extent(W_c, p, lean_half_width)
    if width_count_mode == "center_pitch":
        n_width_tilted = n_width_tilted_center_pitch
    elif width_count_mode == "extent_fit":
        n_width_tilted = n_width_tilted_extent
    else:
        raise ValueError("width_count_mode must be center_pitch or extent_fit.")
    n_width = min(n_width_first, n_width_tilted)
    if n_width <= 0:
        raise ValueError("컨테이너 폭에 타이어가 한 개도 들어가지 않습니다.")

    W1 = tire.D + (n_width - 1) * p
    W2 = n_width * p + p / 2.0
    W3 = n_width * p
    gap = W_c - W2

    # alpha 동적 유도: SW/D 비율 기반
    # sin(α) = sin(α_base) * sqrt((SW/D) / (SW_base/D_base))
    alpha = math.radians(alpha_deg_effective)

    # theta는 30° 고정 (α와 독립적 파라미터 — 접촉 겹침 기하학)
    theta = math.radians(theta_deg)

    R = tire.d / 2.0
    sqrt_term = R**2 - (c / 2.0) ** 2
    if sqrt_term < 0:
        raise ValueError("R^2 - (c/2)^2 값이 음수입니다. c와 d 입력을 확인하세요.")

    a = R - math.sqrt(sqrt_term)
    one_len = a * math.cos(theta)
    two_len = L - one_len
    overlap_height = two_len * math.tan(theta)
    H_pair = 2.0 * tire.D * math.sin(alpha) - overlap_height

    if H_pair <= 0:
        raise ValueError("H_pair가 0 이하입니다. alpha, theta, L 값을 확인하세요.")

    if stack_model not in ("base_layer_pairs", "report_pairs"):
        raise ValueError("stack_model은 base_layer_pairs 또는 report_pairs여야 합니다.")

    if first_layer_count_mode not in ("separate", "tilted_width"):
        raise ValueError("first_layer_count_mode must be separate or tilted_width.")
    if edge_mode not in ("geometry", "none"):
        raise ValueError("edge_mode must be geometry or none.")
    if first_layer_height_mode not in ("legacy", "geometric"):
        raise ValueError("first_layer_height_mode must be legacy or geometric.")

    if stack_model == "base_layer_pairs":
        if first_layer_height_mode == "legacy":
            first_layer_height = max(tire.SW, tire.D * math.sin(alpha))
        else:
            first_layer_height = max(tire.SW, 2.0 * tilted_half_height)
    else:
        first_layer_height = 0.0
    available_after_first_height = H_c - first_layer_height
    if available_after_first_height < 0:
        raise ValueError("컨테이너 높이가 1층 기준 타이어 높이보다 작습니다.")

    repeat_layer_height = H_pair / 2.0
    half_pair_height = repeat_layer_height
    rows_after_first_strict = max(0, math.floor(available_after_first_height / repeat_layer_height))
    rows_after_first_tolerance = max(
        0, math.floor((available_after_first_height + height_tolerance) / repeat_layer_height)
    )
    if n_pair_mode not in ("strict", "tolerance"):
        raise ValueError("n_pair mode must be strict or tolerance.")

    rows_after_first = rows_after_first_tolerance if n_pair_mode == "tolerance" else rows_after_first_strict
    n_pair_strict = rows_after_first_strict // 2
    n_pair_tolerance = rows_after_first_tolerance // 2
    top_single_layer_strict = rows_after_first_strict % 2
    top_single_layer_tolerance = rows_after_first_tolerance % 2
    n_pair = rows_after_first // 2
    top_single_layer = rows_after_first % 2
    if n_pair_mode not in ("strict", "tolerance"):
        raise ValueError("n_pair mode는 strict 또는 tolerance여야 합니다.")
    if rows_after_first <= 0:
        raise ValueError("컨테이너 높이가 부족해 한 쌍도 적재할 수 없습니다.")

    if stack_model != "base_layer_pairs":
        rows_after_first = n_pair * 2
        rows_after_first_strict = n_pair_strict * 2
        rows_after_first_tolerance = n_pair_tolerance * 2
        top_single_layer = 0
        top_single_layer_strict = 0
        top_single_layer_tolerance = 0
    selected_stack_height = first_layer_height + rows_after_first * repeat_layer_height
    strict_stack_height = first_layer_height + rows_after_first_strict * repeat_layer_height
    tolerance_stack_height = first_layer_height + rows_after_first_tolerance * repeat_layer_height
    selected_height_margin = H_c - selected_stack_height
    strict_height_margin = H_c - strict_stack_height
    tolerance_height_margin = H_c - tolerance_stack_height

    if stack_model == "base_layer_pairs":
        n_cross_rows = 1 + rows_after_first
        first_row_count = n_width_first if first_layer_count_mode == "separate" else n_width_tilted
        N_cross = first_row_count + n_width_tilted * rows_after_first
    else:
        first_row_count = n_width
        N_cross = n_width * n_pair * 2
        n_cross_rows = n_pair * 2

    h3_edge = first_layer_height + H_pair
    h_need_edge = tire.SW + tire.D - 2.0 * a
    geometry_edge_left_fit = h_need_edge < h3_edge
    geometry_edge_right_fit = False
    edge_left_fit = geometry_edge_left_fit and edge_mode == "geometry"
    edge_right_fit = geometry_edge_right_fit and edge_mode == "geometry"
    edge_columns = int(edge_left_fit) + int(edge_right_fit)
    edge_start_z = tire.SW
    n_edge_H = edge_columns
    N_edge = edge_columns

    N_face = N_cross + N_edge
    q_L = tire.D
    n_L = math.floor(L_c / q_L)
    if n_L <= 0:
        raise ValueError("컨테이너 길이가 부족해 길이 방향 반복이 불가능합니다.")

    # 실측 테이블 우선 조회 (컨테이너 기본값 사용 시에만 적용)
    N_total = N_face * n_L
    n_total_source = "formula"

    container_fit = W1 <= W_c and W2 <= W_c and W3 <= W_c and selected_stack_height <= H_c + (
        height_tolerance if n_pair_mode == "tolerance" else 0.0
    )

    return {
        "spec": tire.spec,
        "tire": tire,
        "SW_mm": tire.SW_mm,
        "aspect": tire.aspect,
        "rim_inch": tire.rim_inch,
        "SW": tire.SW,
        "d": tire.d,
        "D": tire.D,
        "W_c": W_c,
        "H_c": H_c,
        "L_c": L_c,
        "D_base": D_base,
        "p_base": p_base,
        "c_base": c_base,
        "p_mode": p_mode,
        "p_source": p_source,
        "contact_chord_mode": contact_chord_mode,
        "c_source": c_source,
        "alpha_mode": alpha_mode,
        "alpha_power": alpha_power,
        "width_count_mode": width_count_mode,
        "first_layer_height_mode": first_layer_height_mode,
        "r": r,
        "p": p,
        "c": c,
        "L": L,
        "l_mode": l_mode,
        "alpha_deg": alpha_deg_effective,
        "alpha_deg_input": alpha_deg,
        "theta_deg": theta_deg,
        "n_width": n_width,
        "n_width_first": n_width_first,
        "n_width_even": n_width_even,
        "n_width_odd": n_width_odd,
        "n_width_tilted_center_pitch": n_width_tilted_center_pitch,
        "n_width_tilted_extent": n_width_tilted_extent,
        "n_width_tilted": n_width_tilted,
        "flat_half_width": flat_half_width,
        "lean_half_width": lean_half_width,
        "tilted_half_height": tilted_half_height,
        "W1": W1,
        "W2": W2,
        "W3": W3,
        "gap": gap,
        "cross_y_min": 0.0,
        "cross_y_max": W2,
        "edge_left_gap": p / 2.0,
        "edge_right_gap": W_c - W2,
        "edge_left_fit": edge_left_fit,
        "edge_right_fit": edge_right_fit,
        "edge_start_z": edge_start_z,
        "h3_edge": h3_edge,
        "h_need_edge": h_need_edge,
        "R": R,
        "a": a,
        "one_len": one_len,
        "two_len": two_len,
        "overlap_height": overlap_height,
        "H_pair": H_pair,
        "height_tolerance": height_tolerance,
        "n_pair_strict": n_pair_strict,
        "n_pair_tolerance": n_pair_tolerance,
        "n_pair": n_pair,
        "top_single_layer": top_single_layer,
        "rows_after_first_strict": rows_after_first_strict,
        "rows_after_first_tolerance": rows_after_first_tolerance,
        "rows_after_first": rows_after_first,
        "repeat_layer_height": repeat_layer_height,
        "half_pair_height": half_pair_height,
        "n_pair_mode": n_pair_mode,
        "stack_model": stack_model,
        "first_layer_count_mode": first_layer_count_mode,
        "edge_mode": edge_mode,
        "first_row_count": first_row_count,
        "first_layer_height": first_layer_height,
        "selected_stack_height": selected_stack_height,
        "n_cross_rows": n_cross_rows,
        "strict_height_margin": strict_height_margin,
        "tolerance_height_margin": tolerance_height_margin,
        "selected_height_margin": selected_height_margin,
        "N_cross": N_cross,
        "n_edge_H": n_edge_H,
        "edge_columns": edge_columns,
        "geometry_edge_left_fit": geometry_edge_left_fit,
        "geometry_edge_right_fit": geometry_edge_right_fit,
        "N_edge": N_edge,
        "N_face": N_face,
        "q_L": q_L,
        "n_L": n_L,
        "N_total": N_total,
        "n_total_source": n_total_source,
        "container_fit": container_fit,
    }


def _calculate_n_width(D: float, p: float, W_c: float) -> int:
    """Return the largest n satisfying D + (n - 1) * p <= W_c."""

    if D <= 0 or p <= 0 or W_c <= 0:
        return 0
    if D > W_c:
        return 0
    return 1 + math.floor((W_c - D) / p)


def _validate_positive_dimensions(**values: float) -> None:
    for name, value in values.items():
        if value <= 0:
            raise ValueError(f"{name} 값은 양수여야 합니다.")
