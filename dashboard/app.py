import streamlit as st

st.set_page_config(page_title="Cybersecurity Analytics & AI", page_icon="◉", layout="wide", initial_sidebar_state="expanded")
METRICS=[("Security domains","7","portfolio"),("ML patterns","8","portfolio"),("Graph labs","4","illustrative"),("Detection labs","6","illustrative"),("AI safety labs","5","illustrative"),("OSINT labs","3","illustrative"),("Endpoint labs","4","illustrative"),("Cloud/IAM labs","5","illustrative"),("Synthetic datasets","12","illustrative"),("Notebook validations","18","illustrative"),("Human review","Required","design"),("Production telemetry","0","offline portfolio")]
SIGNALS=[("Detection analytics",.91),("Interpretable ML",.88),("Graph analytics",.84),("AI safety",.86),("Evidence quality",.92)]
st.markdown("""<style>html,body,[class*="css"]{font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Helvetica Neue",Arial,sans-serif;color:#1d1d1f}.stApp{background:#f5f5f7}[data-testid="stHeader"]{background:transparent}[data-testid="stSidebar"]{background:#fff;border-right:1px solid #e5e5ea}.block-container{max-width:1500px;padding:2rem 2.4rem 4rem}.hero{background:linear-gradient(135deg,#fff,#f7fbff);border:1px solid #e5e5ea;border-radius:32px;padding:38px 42px;margin-bottom:24px;box-shadow:0 14px 36px rgba(0,0,0,.045)}.eyebrow{color:#0071e3;font-size:.78rem;font-weight:700;letter-spacing:.11em;text-transform:uppercase}.hero h1{font-size:3.15rem;letter-spacing:-.05em;margin:.22rem 0 .55rem}.hero p{max-width:900px;color:#6e6e73;font-size:1.12rem;line-height:1.55}.pill{display:inline-block;background:#eef6ff;color:#0066cc;border:1px solid #d8eaff;border-radius:999px;padding:.42rem .78rem;margin:.55rem .35rem 0 0;font-size:.76rem;font-weight:650}[data-testid="stMetric"]{background:#fff;border:1px solid #e5e5ea;border-radius:24px;padding:18px 20px;box-shadow:0 8px 26px rgba(0,0,0,.035);min-height:116px}[data-testid="stMetricLabel"]{color:#6e6e73;font-weight:600}[data-testid="stMetricValue"]{font-size:1.9rem;font-weight:700}.stTabs [data-baseweb="tab"]{background:#fff;border:1px solid #e5e5ea;border-radius:999px;padding:8px 16px}.card{background:#fff;border:1px solid #e5e5ea;border-radius:22px;padding:18px 20px}.note{background:#fff;border:1px solid #e5e5ea;border-radius:18px;padding:14px 18px;color:#6e6e73}</style>""",unsafe_allow_html=True)
with st.sidebar:
    st.markdown("## Cybersecurity Analytics & AI"); st.caption("Defensive Security Portfolio"); st.divider(); st.markdown("**Overview**\n\nDetection\n\nML\n\nGraph\n\nAI safety"); st.divider(); st.caption("Offline / synthetic portfolio")
st.markdown("""<div class="hero"><div class="eyebrow">Defensive Security Portfolio</div><h1>Cybersecurity Analytics &amp; AI</h1><p>A consolidated view of detection, interpretable ML, graph analytics, AI safety, OSINT, endpoint, cloud, and identity-security labs.</p><span class="pill">Detection</span><span class="pill">Security ML</span><span class="pill">Graph</span><span class="pill">AI safety</span></div>""",unsafe_allow_html=True)
for s in range(0,len(METRICS),4):
    cols=st.columns(4)
    for c,(l,v,n) in zip(cols,METRICS[s:s+4]): c.metric(l,v,n)
st.subheader("Portfolio health")
l,r=st.columns([1.15,.85],gap="large")
with l:
    for n,v in SIGNALS: st.progress(v,text=f"{n} · {v:.0%}")
with r: st.markdown('<div class="card"><b>Evidence over decoration</b><br><br><span style="color:#6e6e73">Each lab should make assumptions, method, validation, limitations, and analyst takeaways visible rather than hiding behind a model score.</span></div>',unsafe_allow_html=True)
t1,t2,t3,t4=st.tabs(["Detection","ML & anomaly","Graph & identity","AI safety"])
with t1: st.dataframe([{"Area":"SIEM / detection","State":"Portfolio"},{"Area":"Endpoint","State":"Portfolio"},{"Area":"Cloud IAM","State":"Portfolio"}],use_container_width=True,hide_index=True)
with t2:
    for n,v in SIGNALS: st.progress(v,text=n)
with t3: st.dataframe([{"Pattern":"Attack paths","Use":"reachability"},{"Pattern":"Knowledge graphs","Use":"evidence paths"},{"Pattern":"Campaign graphs","Use":"coordination"}],use_container_width=True,hide_index=True)
with t4: st.info("All KPI counts labeled illustrative are portfolio presentation defaults. Individual project repositories remain the source of truth for executable results.")
st.markdown('<div class="note"><b>Evaluation boundary.</b> This is a portfolio-level dashboard and does not claim production efficacy for any component lab.</div>',unsafe_allow_html=True)
