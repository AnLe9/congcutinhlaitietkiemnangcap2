import math
import re

import altair as alt
import pandas as pd
import streamlit as st

st.image("IMG_7764.jpeg")

st.set_page_config(page_title="Sổ tiết kiệm – Công cụ tính lãi", page_icon="📘", layout="wide")

st.title("🌴🥥 Ứng dụng tính lãi gửi tiết kiệm của An Lê Trà Vinh 🥥🌴")
XANH, CAM, LUC = "#60a5fa", "#fbbf24", "#2dd4bf"

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600&family=Source+Serif+4:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'Be Vietnam Pro', sans-serif; }
.stApp { background: #0b1220; }
h1, h2, h3 { font-family: 'Source Serif 4', serif !important; color: #93c5fd; }
.head { border-left: 6px solid #60a5fa; padding: .6rem 1rem; margin-bottom: 1rem; background: linear-gradient(120deg, #12315c, #0f3d47); border-radius: 8px; color: #f1f5f9; }
.head h1 { margin: 0; font-size: 1.7rem; color: #f1f5f9; }
.head p { margin: .2rem 0 0; color: #bfdbfe; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: .7rem; margin: .6rem 0 1rem; }
.card { background: #111c30; border: 1px solid #24344f; border-top: 4px solid #60a5fa; border-radius: 8px; padding: .7rem .9rem; color: #e2e8f0; }
.card.cam { border-top-color: #fbbf24; }
.card.xanh { border-top-color: #2dd4bf; }
.card .l { font-size: .8rem; color: #94a3b8; }
.card .v { font-size: clamp(1.05rem, 2.1vw, 1.4rem); font-weight: 600; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; line-height: 1.25; color: #f1f5f9; }
.card .s { font-size: .75rem; color: #94a3b8; margin-top: .15rem; }
.tbl { max-height: 360px; overflow: auto; border: 1px solid #24344f; border-radius: 8px; margin-bottom: .6rem; }
.tbl table { border-collapse: collapse; width: 100%; font-size: .85rem; color: #e2e8f0; background: #0f1a2e; }
.tbl th { position: sticky; top: 0; background: #1e3a5f; color: #f1f5f9; padding: .45rem .7rem; text-align: right; white-space: nowrap; }
.tbl td { padding: .35rem .7rem; text-align: right; border-bottom: 1px solid #1e2d47; white-space: nowrap; font-variant-numeric: tabular-nums; }
.tbl tr:nth-child(even) td { background: #111c30; }
.tbl th:first-child, .tbl td:first-child { text-align: left; }
.note { border-left: 4px solid #2dd4bf; background: #0d2b2b; color: #99f6e4; padding: .6rem .9rem; border-radius: 6px; margin: .5rem 0; }
</style>
<div class="head"><h1>📘 Sổ tiết kiệm</h1>
<p>Tính lãi, so sánh gói gửi, lập kế hoạch gửi góp và đặt mục tiêu – dựa trên công thức tài chính chuẩn.</p></div>
""",
    unsafe_allow_html=True,
)

# ---------- HÀM DÙNG CHUNG ----------
CHE_DO = {  # (chu kỳ tháng, nhập lãi vào gốc?)
    "Lĩnh lãi cuối kỳ": (None, False),
    "Lĩnh lãi hàng tháng": (1, False),
    "Lĩnh lãi hàng quý": (3, False),
    "Nhập lãi vào gốc hàng tháng (lãi kép)": (1, True),
    "Nhập lãi vào gốc hàng quý (lãi kép)": (3, True),
}


def vnd(x):
    return f"{x:,.0f}".replace(",", ".") + " đ"


def pct(x):
    return f"{x:.2f}%".replace(".", ",")


def doc_tien(x):
    if x >= 1e9:
        return f"≈ {x / 1e9:,.2f} tỷ đồng".replace(",", "·").replace(".", ",").replace("·", ".")
    if x >= 1e6:
        return f"≈ {x / 1e6:,.1f} triệu đồng".replace(",", "·").replace(".", ",").replace("·", ".")
    return f"≈ {x:,.0f} đồng".replace(",", ".")


def dinh_dang(key):
    so = re.sub(r"\D", "", st.session_state[key])
    st.session_state[key] = (f"{int(so):,}".replace(",", ".") + " đ") if so else "0 đ"


def nhap_tien(nhan, key, mac_dinh):
    """Ô nhập tiền: tự thêm dấu chấm hàng nghìn + đơn vị đ khi bấm Enter / bấm ra ngoài."""
    if key not in st.session_state:
        st.session_state[key] = vnd(mac_dinh)
    st.text_input(nhan, key=key, on_change=dinh_dang, args=(key,),
                  help="Gõ số rồi bấm Enter hoặc bấm ra ngoài ô: dấu chấm và chữ 'đ' sẽ tự thêm.")
    v = int(re.sub(r"\D", "", st.session_state[key]) or 0)
    st.caption(doc_tien(v))
    return float(v)


def the(*items):
    """Thẻ kết quả: chữ tự co theo khung, tự xuống dòng, không bao giờ bị cắt '…'."""
    h = ""
    for it in items:
        l, v, s, m = (list(it) + ["", ""])[:4]
        h += f"<div class='card {m}'><div class='l'>{l}</div><div class='v'>{v}</div><div class='s'>{s}</div></div>"
    st.markdown(f"<div class='grid'>{h}</div>", unsafe_allow_html=True)


def bang(df, dp):
    th = "".join(f"<th>{c}</th>" for c in df.columns)
    tr = "".join("<tr>" + "".join(f"<td>{dp.get(c, str)(v)}</td>" for c, v in r.items()) + "</tr>"
                 for r in df.to_dict("records"))
    st.markdown(f"<div class='tbl'><table><tr>{th}</tr>{tr}</table></div>", unsafe_allow_html=True)


def mo_phong(goc, ls, thang, che_do):
    r = ls / 1200
    chu_ky, nhap_goc = CHE_DO[che_do]
    chu_ky = chu_ky or thang
    base, cho, da_nhan, rows = goc, 0.0, 0.0, []
    for t in range(1, thang + 1):
        lai = base * r
        cho += lai
        if t % chu_ky == 0 or t == thang:
            if nhap_goc:
                base += cho
            else:
                da_nhan += cho
            cho = 0.0
        rows.append({"Tháng": t, "Lãi phát sinh": lai, "Lãi tích lũy": base - goc + da_nhan + cho,
                     "Tổng tài sản": base + da_nhan + cho})
    return pd.DataFrame(rows)


def hieu_dung(tong, goc, thang):
    return (tong / goc) ** (12 / thang) - 1 if goc > 0 else 0


def ve(d, a, b, ta, tb):
    x = pd.DataFrame({"Tháng": d["Tháng"], ta: d[a] / 1e6, tb: d[b] / 1e6})
    x = x.melt("Tháng", var_name="Thành phần", value_name="Triệu đồng")
    return (alt.Chart(x).mark_area(opacity=0.9).encode(
        x=alt.X("Tháng:Q"), y=alt.Y("Triệu đồng:Q", stack=True),
        color=alt.Color("Thành phần:N", scale=alt.Scale(domain=[ta, tb], range=[XANH, CAM]),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=["Tháng", "Thành phần", alt.Tooltip("Triệu đồng:Q", format=",.2f")]).properties(height=300))


def grafico(c, **_):
    c = (c.configure(background="transparent")
         .configure_axis(labelColor="#cbd5e1", titleColor="#cbd5e1", gridColor="#1e2d47",
                         domainColor="#334155", tickColor="#334155")
         .configure_legend(labelColor="#e2e8f0", titleColor="#e2e8f0")
         .configure_view(stroke=None))
    st.altair_chart(c, use_container_width=True, theme=None)


FMT = {c: vnd for c in ["Lãi phát sinh", "Lãi tích lũy", "Tổng tài sản", "Tổng đã gửi", "Tiền lãi",
                        "Tổng lãi", "Tổng nhận", "Cần gửi mỗi tháng"]}

# ---------- GIẢ ĐỊNH CHUNG ----------
with st.expander("⚙️ Giả định chung (lạm phát, lãi suất khi rút trước hạn)"):
    g1, g2 = st.columns(2)
    lam_phat = g1.slider("Lạm phát dự kiến (%/năm)", 0.0, 15.0, 3.5, 0.1)
    ls_ktk = g2.slider("Lãi suất không kỳ hạn khi rút trước hạn (%/năm)", 0.0, 2.0, 0.5, 0.05)
    st.caption("Lãi suất tính theo năm, chia đều 12 tháng. Ngân hàng thực tế có thể tính theo số ngày "
               "(365), nên kết quả mang tính tham khảo, không phải lời khuyên đầu tư.")

tab1, tab2, tab_bank, tab3, tab4, tab5 = st.tabs(
    ["💰 Tính lãi", "⚖️ So sánh gói", "🏦 So sánh ngân hàng", "📅 Gửi góp hàng tháng", "🎯 Mục tiêu", "📚 Kiến thức"])

# =====================================================
# TAB 1
# =====================================================
with tab1:
    ca, cb = st.columns([1, 2], gap="large")
    with ca:
        goc = nhap_tien("Số tiền gửi", "t1_goc", 100_000_000)
        thang = st.slider("Kỳ hạn (tháng)", 1, 120, 12, key="t1_thang")
        ls = st.number_input("Lãi suất (%/năm)", 0.0, 30.0, 5.5, 0.1, format="%.2f", key="t1_ls")
        che_do = st.selectbox("Hình thức nhận lãi", list(CHE_DO), key="t1_cd")
        st.caption("Lĩnh lãi = lãi đơn (lãi luôn tính trên gốc ban đầu). "
                   "Nhập lãi vào gốc = lãi kép (có lãi trên lãi).")

    df = mo_phong(goc, ls, thang, che_do)
    tong = df["Tổng tài sản"].iloc[-1]
    lai_tong = tong - goc
    chu_ky, nhap_goc = CHE_DO[che_do]
    ck = min(chu_ky or thang, thang)
    ear = hieu_dung(tong, goc, thang)
    thuc = (1 + ear) / (1 + lam_phat / 100) - 1
    suc_mua = tong / (1 + lam_phat / 100) ** (thang / 12)
    gap_doi = math.log(2) / math.log(1 + ear) if ear > 0 else None

    with cb:
        if nhap_goc:
            o1 = ("Lãi nhập vào gốc", "Tự động", "mỗi kỳ, không rút ra")
        else:
            tn = "kỳ hạn" if ck == thang else ("tháng" if ck == 1 else "quý")
            o1 = (f"Lãi nhận mỗi {tn}", vnd(goc * ls / 1200 * ck))
        the(o1, ("Tổng tiền lãi", vnd(lai_tong), "", "xanh"), ("Tổng gốc + lãi", vnd(tong), "cuối kỳ hạn", "cam"),
            ("Lợi suất hiệu dụng", pct(ear * 100) + "/năm", "đã tính lãi trên lãi"),
            ("Lãi suất thực (sau lạm phát)", pct(thuc * 100) + "/năm", "Fisher: (1+r)/(1+π) − 1"),
            ("Sức mua cuối kỳ", vnd(suc_mua), "quy về giá trị hôm nay"),
            ("Thời gian để tiền gấp đôi", f"{gap_doi:.1f} năm".replace(".", ",") if gap_doi else "—",
             "nếu giữ nguyên lợi suất"))
        if thuc < 0:
            st.warning(f"Lạm phát {lam_phat:.1f}%/năm đang cao hơn lợi suất: tiền của bạn **mất giá thực tế**.")
        else:
            st.markdown(f"<div class='note'>Sau lạm phát, tiền của bạn tăng giá trị thực khoảng "
                        f"<b>{pct(thuc * 100)}/năm</b>.</div>", unsafe_allow_html=True)

    grafico(ve(df.assign(Gốc=goc), "Gốc", "Lãi tích lũy", "Vốn gốc", "Tiền lãi"), use_container_width=True)

    if thang > 2:
        with st.expander("⏱️ Nếu rút trước hạn thì sao?"):
            k = st.slider("Rút ở tháng thứ", 1, thang - 1, max(1, thang // 2), key="t1_k")
            nhan = goc * (1 + ls_ktk / 1200 * k)
            the(("Số tiền nhận khi rút", vnd(nhan), f"lãi không kỳ hạn {pct(ls_ktk)}/năm"),
                ("Lãi thực nhận", vnd(nhan - goc), "", "xanh"),
                ("Thiệt hại so với đủ kỳ hạn", vnd(tong - nhan), "", "cam"))

    with st.expander("📑 Bảng chi tiết từng tháng"):
        bang(df, FMT)
    st.download_button("⬇️ Tải bảng chi tiết (CSV)", df.to_csv(index=False).encode("utf-8-sig"),
                       "chi_tiet_lai_tiet_kiem.csv", "text/csv")

# =====================================================
# TAB 2
# =====================================================
with tab2:
    st.write("So sánh tối đa 3 gói với cùng số tiền gửi. Dùng **lợi suất hiệu dụng/năm** để so công bằng "
             "khi kỳ hạn hoặc cách trả lãi khác nhau.")
    goc2 = nhap_tien("Số tiền gửi", "t2_goc", 100_000_000)
    md = [("Gói A", 5.0, 6), ("Gói B", 5.8, 12), ("Gói C", 6.2, 24)]
    rows = []
    for i, col in enumerate(st.columns(3)):
        with col:
            ten = st.text_input("Tên gói", md[i][0], key=f"t2_ten{i}")
            l = st.number_input("Lãi suất (%/năm)", 0.0, 30.0, md[i][1], 0.1, key=f"t2_ls{i}")
            k = st.number_input("Kỳ hạn (tháng)", 1, 120, md[i][2], key=f"t2_k{i}")
            cd = st.selectbox("Nhận lãi", list(CHE_DO), key=f"t2_cd{i}")
        t = mo_phong(goc2, l, k, cd)["Tổng tài sản"].iloc[-1]
        rows.append({"Gói": ten, "Kỳ hạn (tháng)": k, "Lãi suất": l, "Tổng lãi": t - goc2, "Tổng nhận": t,
                     "Lợi suất hiệu dụng": hieu_dung(t, goc2, k) * 100})
    kq = pd.DataFrame(rows)
    tot = kq.loc[kq["Lợi suất hiệu dụng"].idxmax()]
    the(("Gói có lợi suất hiệu dụng cao nhất", tot["Gói"], pct(tot["Lợi suất hiệu dụng"]) + "/năm", "xanh"),
        ("Gói cho nhiều tiền lãi nhất", kq.loc[kq["Tổng lãi"].idxmax(), "Gói"],
         vnd(kq["Tổng lãi"].max()) + " (kỳ hạn dài thì khóa tiền lâu hơn)", "cam"))
    bang(kq, {**FMT, "Lãi suất": pct, "Lợi suất hiệu dụng": pct})
    grafico(alt.Chart(kq).mark_bar(color=XANH, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X("Gói:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Lợi suất hiệu dụng:Q", title="% / năm"),
        tooltip=["Gói", alt.Tooltip("Lợi suất hiệu dụng:Q", format=".2f")]).properties(height=240),
        use_container_width=True)

# =====================================================
# TAB 3
# =====================================================
with tab3:
    ca, cb = st.columns([1, 2], gap="large")
    with ca:
        von = nhap_tien("Vốn ban đầu", "t3_dau", 0)
        gop = nhap_tien("Gửi thêm mỗi tháng", "t3_gop", 5_000_000)
        n3 = st.slider("Thời gian (tháng)", 1, 360, 60, key="t3_n")
        ls3 = st.number_input("Lãi suất (%/năm)", 0.0, 30.0, 6.0, 0.1, key="t3_ls")
        tang = st.number_input("Mỗi năm tăng tiền gửi thêm (%)", 0.0, 50.0, 0.0, 1.0,
                               help="Ví dụ thu nhập tăng 10%/năm thì bạn gửi nhiều hơn 10%/năm.")
    sd, dg, rows = von, von, []
    for t in range(1, n3 + 1):
        g = gop * (1 + tang / 100) ** ((t - 1) // 12)
        sd = (sd + g) * (1 + ls3 / 1200)  # gửi đầu tháng, lãi nhập gốc hàng tháng
        dg += g
        rows.append({"Tháng": t, "Tổng đã gửi": dg, "Tiền lãi": sd - dg, "Tổng tài sản": sd})
    d3 = pd.DataFrame(rows)
    with cb:
        the(("Tổng tiền bạn đã gửi", vnd(dg)), ("Tiền lãi sinh ra", vnd(sd - dg), "", "xanh"),
            ("Tổng tài sản", vnd(sd), "", "cam"),
            ("Sức mua thực", vnd(sd / (1 + lam_phat / 100) ** (n3 / 12)), f"quy về giá hôm nay, lạm phát {lam_phat:.1f}%"))
        grafico(ve(d3, "Tổng đã gửi", "Tiền lãi", "Tiền bạn gửi", "Tiền lãi sinh ra"), use_container_width=True)
    with st.expander("📑 Bảng chi tiết"):
        bang(d3, FMT)

# =====================================================
# TAB 4
# =====================================================
with tab4:
    ca, cb = st.columns([1, 2], gap="large")
    with ca:
        mt = nhap_tien("Số tiền muốn có", "t4_mt", 500_000_000)
        cs = nhap_tien("Số tiền đã có", "t4_cs", 50_000_000)
        n4 = st.slider("Thời hạn (tháng)", 1, 360, 60, key="t4_n")
        ls4 = st.number_input("Lãi suất kỳ vọng (%/năm)", 0.0, 30.0, 6.0, 0.1, key="t4_ls")

    def can_gop(rn):
        i = rn / 1200
        if i == 0:
            return max(mt - cs, 0) / n4
        f = (1 + i) ** n4
        return max((mt - cs * f) * i / ((f - 1) * (1 + i)), 0)

    with cb:
        m = can_gop(ls4)
        if m == 0:
            st.success("🎉 Chỉ cần giữ số tiền đang có, bạn đã đạt mục tiêu trong thời hạn này.")
        else:
            the(("Cần gửi mỗi tháng", vnd(m), "", "cam"), ("Tổng bạn bỏ ra", vnd(cs + m * n4)),
                ("Lãi sinh ra giúp bạn", vnd(mt - cs - m * n4), "", "xanh"),
                ("Mục tiêu theo giá hôm nay", vnd(mt / (1 + lam_phat / 100) ** (n4 / 12)),
                 "sức mua thực sau lạm phát"))
        st.write("**Nếu lãi suất thay đổi thì sao?**")
        bang(pd.DataFrame({"Lãi suất": [max(ls4 - 2, 0), ls4, ls4 + 2],
                           "Cần gửi mỗi tháng": [can_gop(max(ls4 - 2, 0)), m, can_gop(ls4 + 2)]}),
             {**FMT, "Lãi suất": pct})

# =====================================================
# TAB 5
# =====================================================
with tab5:
    st.subheader("Các công thức đứng sau ứng dụng")
    st.markdown("**Lãi đơn** – lãi chỉ tính trên vốn gốc:")
    st.latex(r"A = P\,(1 + r\,t)")
    st.markdown("**Lãi kép** – lãi được nhập vào gốc $m$ lần mỗi năm, sinh ra lãi trên lãi:")
    st.latex(r"A = P\left(1 + \frac{r}{m}\right)^{m\,t}")
    st.markdown("**Lợi suất hiệu dụng (EAR)** – thước đo công bằng để so sánh các gói khác nhau:")
    st.latex(r"\mathrm{EAR} = \left(\frac{A}{P}\right)^{1/t} - 1")
    st.markdown("**Lãi suất thực (Fisher)** – lãi thật sự sau khi trừ lạm phát $\\pi$:")
    st.latex(r"r_{thực} = \frac{1 + r}{1 + \pi} - 1")
    st.markdown("**Gửi góp đầu mỗi tháng** – $M$ là tiền gửi mỗi tháng, $i = r/12$:")
    st.latex(r"FV = M\cdot\frac{(1+i)^n - 1}{i}\,(1+i)")
    st.markdown("**Quy tắc 72** – ước lượng nhanh số năm để tiền gấp đôi:")
    st.latex(r"t \approx \frac{72}{r\,(\%)}")
    st.subheader("Lưu ý khi gửi tiết kiệm")
    st.markdown(
        "- Lãi suất cao hơn chưa chắc tốt hơn nếu **thấp hơn lạm phát**: tiền vẫn mất giá thực tế.\n"
        "- Rút trước hạn thường chỉ được hưởng **lãi suất không kỳ hạn**, rất thấp. Đừng khóa số tiền bạn có thể cần gấp.\n"
        "- Chia nhỏ khoản gửi theo nhiều kỳ hạn giúp vừa có lãi tốt vừa linh hoạt khi cần tiền.\n"
        "- Kiểm tra mức bảo hiểm tiền gửi và độ uy tín của tổ chức tín dụng trước khi gửi số tiền lớn.\n"
        "- Công cụ này chỉ mang tính tham khảo; hãy đối chiếu với biểu lãi suất và hợp đồng của ngân hàng."
    )

# =====================================================
# TAB SO SÁNH NGÂN HÀNG
# =====================================================
with tab_bank:
    st.write("Bảng dưới là lãi suất **tiết kiệm thường tại quầy**, niêm yết ngày 1/10/2026 "
             "(nguồn: Tạp chí Thị trường Tài chính Tiền tệ). Bạn có thể **sửa trực tiếp**, thêm ngân hàng "
             "ở dòng cuối; ô trống nghĩa là chưa có số liệu. Đơn vị: %/năm.")
    mau = pd.DataFrame([
        ["Vietcombank", 3.5, 3.5, 5.9, 6.0],
        ["BIDV", 3.5, 3.5, 5.9, 6.0],
        ["VietinBank", 3.5, 3.5, 5.9, 6.0],
        ["PVcomBank", None, None, 5.6, None],
        ["GPBank", None, None, 5.55, None],
        ["KienlongBank", None, None, 5.5, None],
        ["Eximbank", None, None, 5.3, None],
        ["HDBank", None, None, 5.3, None],
        ["SeABank", None, None, 5.0, None],
        ["SCB", None, None, 3.7, None],
    ], columns=["Ngân hàng", "6 tháng", "9 tháng", "12 tháng", "24 tháng"])
    ls_bang = st.data_editor(
        mau, num_rows="dynamic", hide_index=True, use_container_width=True, key="bank_tbl",
        column_config={c: st.column_config.NumberColumn(c, format="%.2f", min_value=0.0, max_value=20.0, step=0.05)
                       for c in mau.columns[1:]})
    b1, b2 = st.columns(2)
    with b1:
        goc_b = nhap_tien("Số tiền gửi", "bk_goc", 100_000_000)
    with b2:
        ky = st.selectbox("Kỳ hạn muốn so sánh", ["6 tháng", "9 tháng", "12 tháng", "24 tháng"], index=2)
    thang_b = int(ky.split()[0])

    d = ls_bang.dropna(subset=["Ngân hàng", ky]).copy()
    d = d[d["Ngân hàng"].astype(str).str.strip() != ""]
    if d.empty:
        st.info("Chưa có ngân hàng nào có lãi suất cho kỳ hạn này. Hãy nhập thêm vào bảng ở trên.")
    else:
        d["Lãi suất"] = d[ky].astype(float)
        d["Tổng lãi"] = goc_b * d["Lãi suất"] / 100 * thang_b / 12  # lãi đơn, lĩnh cuối kỳ
        d["Tổng nhận"] = goc_b + d["Tổng lãi"]
        d = d.sort_values("Tổng lãi", ascending=False).reset_index(drop=True)
        d.insert(0, "Hạng", d.index + 1)
        top, bot = d.iloc[0], d.iloc[-1]
        the(("Lãi suất cao nhất", top["Ngân hàng"], f"{pct(top['Lãi suất'])}/năm", "xanh"),
            ("Tiền lãi nhận được", vnd(top["Tổng lãi"]), f"sau {thang_b} tháng"),
            ("Chênh lệch so với thấp nhất", vnd(top["Tổng lãi"] - bot["Tổng lãi"]),
             f"so với {bot['Ngân hàng']} ({pct(bot['Lãi suất'])})", "cam"))
        bang(d[["Hạng", "Ngân hàng", "Lãi suất", "Tổng lãi", "Tổng nhận"]], {**FMT, "Lãi suất": pct})
        grafico(alt.Chart(d).mark_bar(color=XANH, cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
            y=alt.Y("Ngân hàng:N", sort="-x", title=None), x=alt.X("Lãi suất:Q", title="% / năm"),
            tooltip=["Ngân hàng", alt.Tooltip("Lãi suất:Q", format=".2f"),
                     alt.Tooltip("Tổng lãi:Q", format=",.0f")]).properties(height=max(120, 34 * len(d))))
    st.markdown("<div class='note'>Lưu ý: lãi suất đổi theo từng thời điểm và từng kênh (quầy, online). "
                "Chứng chỉ tiền gửi thường có lãi cao hơn tiền gửi thường khoảng 1–3 điểm %, nhưng là sản phẩm khác "
                "(điều kiện chuyển nhượng, rút trước hạn), hãy hỏi kỹ ngân hàng trước khi gửi.</div>",
                unsafe_allow_html=True)
