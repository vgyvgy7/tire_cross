import pandas as pd
import streamlit as st

from calc import calculate_loading
from visualize import create_stack_figure


st.set_page_config(page_title="40HFT Tire Cross Stack", layout="wide")


def _format_value(value):
    if isinstance(value, float):
        return f"{value:,.2f}"
    return value


def _metrics_table(result):
    rows = [
        ("입력 타이어 규격", result["spec"], ""),
        ("SW", result["SW"], "cm"),
        ("림 직경 d", result["d"], "cm"),
        ("외경 D", result["D"], "cm"),
        ("스케일 r", result["r"], ""),
        ("폭 방향 전진량 p", result["p"], "cm"),
        ("p mode", result["p_mode"], ""),
        ("p source", result["p_source"], ""),
        ("접촉 현 길이 c", result["c"], "cm"),
        ("c source", result["c_source"], ""),
        ("높이 공식 L", result["L"], "cm"),
        ("n_width", result["n_width"], "개"),
        ("n_width_tilted", result["n_width_tilted"], "개"),
        ("n_width_tilted_center_pitch", result["n_width_tilted_center_pitch"], "개"),
        ("n_width_tilted_extent", result["n_width_tilted_extent"], "개"),
        ("lean half width", result["lean_half_width"], "cm"),
        ("tilted half height", result["tilted_half_height"], "cm"),
        ("Row 1 폭 W1", result["W1"], "cm"),
        ("Row 2 폭 W2", result["W2"], "cm"),
        ("gap", result["gap"], "cm"),
        ("left edge actual gap", result["edge_left_gap"], "cm"),
        ("right edge actual gap", result["edge_right_gap"], "cm"),
        ("left edge fit", "yes" if result["edge_left_fit"] else "no", ""),
        ("right edge fit", "yes" if result["edge_right_fit"] else "no", ""),
        ("edge start z", result["edge_start_z"], "cm"),
        ("edge h_need", result["h_need_edge"], "cm"),
        ("edge h3", result["h3_edge"], "cm"),
        ("a", result["a"], "cm"),
        ("one_len", result["one_len"], "cm"),
        ("two_len", result["two_len"], "cm"),
        ("overlap_height", result["overlap_height"], "cm"),
        ("H_pair", result["H_pair"], "cm"),
        ("repeat layer height", result["repeat_layer_height"], "cm"),
        ("rows after first", result["rows_after_first"], "rows"),
        ("top single layer", result["top_single_layer"], "?"),
        ("half pair height", result["half_pair_height"], "cm"),
        ("strict 기준 n_pair", result["n_pair_strict"], "쌍"),
        ("tolerance 적용 n_pair", result["n_pair_tolerance"], "쌍"),
        ("최종 사용 n_pair", result["n_pair"], "쌍"),
        ("stack model", result["stack_model"], ""),
        ("first layer count mode", result["first_layer_count_mode"], ""),
        ("first row count", result["first_row_count"], "개"),
        ("edge mode", result["edge_mode"], ""),
        ("contact chord mode", result["contact_chord_mode"], ""),
        ("alpha mode", result["alpha_mode"], ""),
        ("alpha power", result["alpha_power"], ""),
        ("alpha input", result["alpha_deg_input"], "deg"),
        ("alpha effective", result["alpha_deg"], "deg"),
        ("width count mode", result["width_count_mode"], ""),
        ("first layer height mode", result["first_layer_height_mode"], ""),
        ("1층 기준 높이", result["first_layer_height"], "cm"),
        ("선택 기준 총 stack 높이", result["selected_stack_height"], "cm"),
        ("크로스 row 수", result["n_cross_rows"], "줄"),
        ("strict 초과/여유 높이", result["strict_height_margin"], "cm"),
        ("tolerance 초과/여유 높이", result["tolerance_height_margin"], "cm"),
        ("선택 기준 초과/여유 높이", result["selected_height_margin"], "cm"),
        ("N_cross", result["N_cross"], "개/단면"),
        ("edge column 수", result["edge_columns"], "열"),
        ("n_edge_H", result["n_edge_H"], "개/측면"),
        ("N_edge", result["N_edge"], "개/단면"),
        ("N_face", result["N_face"], "개/단면"),
        ("n_L", result["n_L"], "층"),
        ("N_total", result["N_total"], "개"),
        ("컨테이너 적합 여부", "적합" if result["container_fit"] else "초과", ""),
    ]
    return pd.DataFrame(rows, columns=["항목", "값", "단위"])


with st.sidebar:
    st.header("Input")
    preset_spec = st.selectbox(
        "Tire preset",
        [
            "205/55R16",
            "215/55R17",
            "225/45R17",
            "235/45R18",
            "235/50R19",
            "195/65R15",
            "235/60R18",
            "255/45R20",
            "Custom",
        ],
        index=0,
    )
    if preset_spec == "Custom":
        tire_spec = st.text_input("Tire spec", value="205/55R16", help="Format: 205/55R16")
    else:
        tire_spec = preset_spec
        st.caption(f"Using tire spec: {tire_spec}")

    st.divider()
    st.subheader("Container (cm)")
    W_c = st.number_input("Inside width W_c", min_value=1.0, value=235.0, step=0.5)
    H_c = st.number_input("Inside height H_c", min_value=1.0, value=270.0, step=0.5)
    L_c = st.number_input("Inside length L_c", min_value=1.0, value=1203.0, step=1.0)

    st.divider()
    st.subheader("Cross stack geometry")
    alpha_deg = st.number_input("Base tilt angle alpha (deg)", min_value=0.1, max_value=89.9, value=30.0, step=0.5)
    alpha_mode = st.selectbox(
        "Alpha mode",
        ["sin_sqrt_sw_d", "dynamic_sqrt_sw_od", "asin_sw_d", "manual", "sw_d_proportional", "sw_d_power"],
        index=0,
        help="sin_sqrt_sw_d sets sin(alpha)=sin(alpha_base)*sqrt((SW/D)/(21.5/D_base)).",
    )
    alpha_power = st.number_input("Alpha power", min_value=0.01, max_value=2.0, value=0.32, step=0.01)
    theta_deg = st.number_input("Overlap angle theta (deg)", min_value=0.1, max_value=89.9, value=30.0, step=0.5)
    p_mode = st.selectbox(
        "Pitch p mode",
        ["scaled_base", "manual", "measured_table"],
        index=0,
        help="scaled_base uses p=45cm as the 215/55R17 base value and scales by D/D_base.",
    )
    p_base = st.number_input("Base width pitch p_base", min_value=0.1, value=45.0, step=0.5)
    contact_chord_mode = st.selectbox(
        "Contact chord c mode",
        ["scaled_base", "manual", "measured_table"],
        index=0,
        help="scaled_base uses c=30cm as the 215/55R17 base value and scales by D/D_base.",
    )
    c_base = st.number_input("Contact chord c / c_base", min_value=0.1, value=30.0, step=0.5)
    l_mode = st.selectbox("Height formula L mode", ["scaled_p", "base_45", "manual"], index=0)
    manual_l = st.number_input("Manual L", min_value=0.1, value=45.0, step=0.5)
    height_tolerance = st.number_input("Height tolerance", min_value=0.0, value=1.5, step=0.1)
    n_pair_mode = st.selectbox("Height count mode", ["tolerance", "strict"], index=0)
    stack_model = st.selectbox("Stack model", ["base_layer_pairs", "report_pairs"], index=0)
    width_count_mode = st.selectbox(
        "Width count check",
        ["center_pitch", "extent_fit"],
        index=0,
        help="extent_fit checks the tilted tire outer envelope against container width.",
    )
    first_layer_height_mode = st.selectbox(
        "First layer height",
        ["legacy", "geometric"],
        index=0,
        help="geometric uses the tilted tire envelope height so the first layer does not pass below the floor.",
    )
    first_layer_count_mode = st.selectbox(
        "First row count",
        ["separate", "tilted_width"],
        index=0,
        help="separate uses n_width_first for the first row. tilted_width uses n_width_tilted for the first row too.",
    )
    edge_mode = st.selectbox(
        "Side edge tires",
        ["geometry", "none"],
        index=0,
        help="geometry includes side edge tires when the geometric check allows them.",
    )

    st.divider()
    st.subheader("View")
    render_mode = st.selectbox("Render mode", ["front_only", "sample_layers", "full"], index=0)
    realistic_tire_mesh = st.checkbox("Realistic tire mesh", value=True)
    tread_detail = st.checkbox("Tread detail", value=True)
    mesh_quality = st.selectbox("Mesh quality", ["low", "medium", "high"], index=1)
    tire_opacity = st.slider("Tire opacity", min_value=0.15, max_value=1.0, value=0.82, step=0.01)
    show_container = st.checkbox("Show container", value=True)
    show_edge_tires = st.checkbox("Show edge tires", value=True)
    show_calculation_table = st.checkbox("Show calculation table", value=True)

st.title("40HFT 컨테이너 타이어 꽈배기/크로스 적재 계산기")
st.caption("3D 시각화는 보고서 수식 기반 근사 배치이며 실제 충돌 물리 시뮬레이션이 아닙니다.")

try:
    result = calculate_loading(
        tire_spec,
        W_c=W_c,
        H_c=H_c,
        L_c=L_c,
        p_base=p_base,
        c_base=c_base,
        alpha_deg=alpha_deg,
        theta_deg=theta_deg,
        l_mode=l_mode,
        manual_l=manual_l,
        height_tolerance=height_tolerance,
        n_pair_mode=n_pair_mode,
        stack_model=stack_model,
        first_layer_count_mode=first_layer_count_mode,
        edge_mode=edge_mode,
        p_mode=p_mode,
        contact_chord_mode=contact_chord_mode,
        alpha_mode=alpha_mode,
        alpha_power=alpha_power,
        width_count_mode=width_count_mode,
        first_layer_height_mode=first_layer_height_mode,
    )
except ValueError as exc:
    st.error(str(exc))
    st.stop()

summary_cols = st.columns(5)
summary_cols[0].metric("n_width", int(result["n_width"]))
summary_cols[1].metric("rows above 1st", int(result["rows_after_first"]))
summary_cols[2].metric("N_face", int(result["N_face"]))
summary_cols[3].metric("n_L", int(result["n_L"]))
summary_cols[4].metric("N_total", f"{int(result['N_total']):,}")

st.caption(
    "N_cross = first_row_count + n_width_tilted * rows_after_first = "
    f"{int(result['first_row_count'])} + {int(result['n_width_tilted'])} * "
    f"{int(result['rows_after_first'])} = {int(result['N_cross'])}; "
    f"N_face = N_cross + N_edge = {int(result['N_face'])}; "
    f"N_total = N_face * n_L = {int(result['N_total'])}"
)

section_tab, total_tab, calc_tab = st.tabs(["단면 적재", "전체 적재량", "계산 결과"])

with section_tab:
    st.subheader("단면 3D tire mesh")
    st.caption(
        "한 단면의 꽈배기 적재를 실제 타이어 mesh로 보여줍니다. "
        "배치는 보고서 수식 기반 근사이며 실제 물리 충돌 계산은 수행하지 않습니다."
    )
    fig = create_stack_figure(
        result,
        render_mode=render_mode,
        realistic_tire_mesh=realistic_tire_mesh,
        tread_detail=tread_detail,
        mesh_quality=mesh_quality,
        tire_opacity=tire_opacity,
        show_container=show_container,
        show_edge_tires=show_edge_tires,
    )
    st.plotly_chart(fig, use_container_width=True)

with total_tab:
    st.subheader("전체 적재량")
    total_cols = st.columns(4)
    total_cols[0].metric("단면 적재 N_face", f"{int(result['N_face']):,}")
    total_cols[1].metric("길이 방향 n_L", f"{int(result['n_L']):,}")
    total_cols[2].metric("총 적재 N_total", f"{int(result['N_total']):,}")
    total_cols[3].metric("컨테이너", "적합" if result["container_fit"] else "초과")
    st.caption(
        f"N_total = N_face × n_L = {int(result['N_face']):,} × "
        f"{int(result['n_L']):,} = {int(result['N_total']):,}"
    )
    st.caption(
        "아래 그림은 길이 방향 반복 구조를 앞쪽 3줄로 샘플 표시합니다. "
        "전체 적재량은 19줄 전체를 기준으로 계산됩니다."
    )
    total_fig = create_stack_figure(
        result,
        render_mode="sample_layers",
        realistic_tire_mesh=True,
        tread_detail=False,
        mesh_quality="low",
        tire_opacity=0.68,
        show_container=show_container,
        show_edge_tires=show_edge_tires,
    )
    st.plotly_chart(total_fig, use_container_width=True)
    if st.button("19줄 전체 3D 렌더링", help="전체 mesh 렌더링은 타이어 수가 많아 느릴 수 있습니다."):
        full_fig = create_stack_figure(
            result,
            render_mode="full",
            realistic_tire_mesh=True,
            tread_detail=False,
            mesh_quality="low",
            tire_opacity=0.58,
            show_container=show_container,
            show_edge_tires=show_edge_tires,
        )
        st.plotly_chart(full_fig, use_container_width=True)

with calc_tab:
    if show_calculation_table:
        st.subheader("계산 결과")
        table = _metrics_table(result)
        display_table = table.copy()
        display_table["값"] = display_table["값"].map(_format_value)
        st.dataframe(display_table, use_container_width=True, hide_index=True)

with st.expander("205/55R16 검산 포인트", expanded=False):
    st.write(
        "기본 stack model은 `base_layer_pairs`입니다. 1층을 별도 기준층으로 두고, "
        "2-3층/4-5층/...만 꽈배기 pair로 계산합니다. "
        "사이드 타이어는 실제 좌우 빈 폭이 SW 이상일 때만 계산/표시합니다."
    )

with st.expander("층별 꽈배기 수식", expanded=False):
    st.markdown(
        """
        기본 계산은 `1층 단독 + (2,3층), (4,5층), ... 꽈배기 pair` 모델입니다.
        1층만 첫 번째 타이어를 편평하게 두고, 2층 이상은 첫 타이어부터 모두 기울어진 타이어로 계산합니다.

        ```text
        H_pair = 2 * D * sin(alpha) - overlap_height

        overlap_height = (L - a*cos(theta)) * tan(theta)
        a = d/2 - sqrt((d/2)^2 - (c/2)^2)
        ```

        1층:

        ```text
        first_layer_height = max(SW, D * sin(alpha))
        z_1_center = first_layer_height / 2
        y_i = D/2 + i*p
        i = 0 orientation = 0도, i >= 1 orientation = +alpha
        n_width_first = max n such that D + (n - 1)*p <= W_c
        ```

        2,3층 pair (`k=1`):

        ```text
        z_pair_base_1 = D
        z_2_center = z_pair_base_1 + H_pair/4
        z_3_center = z_pair_base_1 + 3*H_pair/4
        ```

        4,5층 pair (`k=2`):

        ```text
        z_pair_base_2 = D + H_pair
        z_4_center = z_pair_base_2 + H_pair/4
        z_5_center = z_pair_base_2 + 3*H_pair/4
        ```

        일반식 (`k=1, 2, 3, ...`):

        ```text
        z_pair_base_k = D + (k-1)*H_pair
        z_lower_center = z_pair_base_k + H_pair/4
        z_upper_center = z_pair_base_k + 3*H_pair/4

        Row lower: orientation = +alpha for every i
        Row upper: orientation = -alpha for every i
        n_width_tilted = floor(W_c / p)
        ```

        이 모델은 1층을 별도로 빼므로 기존 보고서 재현용 `report_pairs` 모델보다 총량이 줄어듭니다.
        `report_pairs`는 기존 보고서의 pair 계산 방식만 비교할 때 사용합니다.
        사이드 타이어는 실제 좌우 빈 폭이 SW 이상일 때만 추가합니다.
        """
    )
