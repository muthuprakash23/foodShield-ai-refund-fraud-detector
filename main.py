import streamlit as st
import uuid
import os
import tempfile
from graph import fraud_graph
from state import FraudState

st.set_page_config(
    page_title="Food Complaint Fraud Detector",
    page_icon="🍽️",
    layout="wide",
)

# --- Session State Init ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "order_id" not in st.session_state:
    st.session_state.order_id = None
if "image_path" not in st.session_state:
    st.session_state.image_path = None
if "awaiting_human_review" not in st.session_state:
    st.session_state.awaiting_human_review = False
if "fraud_state" not in st.session_state:
    st.session_state.fraud_state = None
if "final_result" not in st.session_state:
    st.session_state.final_result = None


def get_field(result, field, default=None):
    if isinstance(result, dict):
        return result.get(field, default)
    return getattr(result, field, default)


def run_graph_turn(user_message: str = None, image_path: str = None):
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    # --- Preserve previous state ---
    if st.session_state.fraud_state is not None:
        if isinstance(st.session_state.fraud_state, dict):
            data = dict(st.session_state.fraud_state)
        else:
            data = st.session_state.fraud_state.model_dump()
    else:
        data = {}

    data["user_id"] = st.session_state.user_id
    data["order_id"] = st.session_state.order_id
    data["complaint_text"] = user_message
    data["image_path"] = image_path or st.session_state.image_path

    state = FraudState(**data)
    result = fraud_graph.invoke(state, config=config)

    st.session_state.fraud_state = result
    return result


def resume_graph():
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    result = fraud_graph.invoke(None, config=config)
    st.session_state.fraud_state = result
    return result


# --- UI ---
st.title("🍽️ Food Complaint Fraud Detection System")
st.caption("Powered by LangGraph · Gemini · Groq · HuggingFace")

# --- Sidebar ---
with st.sidebar:
    st.header("🔐 Session Details")
    st.caption("Enter your details to begin a complaint")

    user_id = st.text_input("User ID", placeholder="e.g. USR001",
                            value=st.session_state.user_id or "")
    order_id = st.text_input("Order ID", placeholder="e.g. ORD024",
                             value=st.session_state.order_id or "")

    if st.button("Start Complaint Session", type="primary"):
        if user_id and order_id:
            st.session_state.user_id = user_id.upper()
            st.session_state.order_id = order_id.upper()
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.awaiting_human_review = False
            st.session_state.fraud_state = None
            st.session_state.final_result = None
            st.session_state.image_path = None
            st.success(f"Session started for {user_id.upper()}")
        else:
            st.error("Please enter both User ID and Order ID")

    st.divider()
    st.caption("🧪 Test Users")
    st.markdown("""
    | User | Profile |
    |------|---------|
    | USR001 | Clean user |
    | USR002 | Moderate |
    | USR003 | Very clean |
    | USR004 | Fraud user |
    | USR005 | New account |
    """)
    st.divider()
    if st.button("🔄 Reset Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- Guard ---
if not st.session_state.user_id or not st.session_state.order_id:
    st.info("👈 Please enter your User ID and Order ID in the sidebar to begin.")
    st.stop()

# --- Chat Display ---
st.subheader("💬 Complaint Chat")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- Image Upload ---
if not st.session_state.final_result:
    uploaded_file = st.file_uploader(
        "📸 Upload complaint image",
        type=["jpg", "jpeg", "png"],
        key="image_uploader",
    )
    if uploaded_file and not st.session_state.image_path:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            st.session_state.image_path = tmp.name

        st.success("✅ Image uploaded successfully")
        st.image(uploaded_file, caption="Uploaded complaint image", width=300)

        
        with st.spinner("Processing image..."):
            try:
                result = run_graph_turn(
                    user_message=None,
                    image_path=st.session_state.image_path,
                )

                next_step = get_field(result, "next_step")
                messages = get_field(result, "messages") or []

                if messages:
                    last = messages[-1]
                    if isinstance(last, dict):
                        msg_type = last.get("type")
                        msg_content = last.get("content", "")
                    else:
                        msg_type = getattr(last, "type", "")
                        msg_content = getattr(last, "content", "")

                    if msg_type == "ai" and msg_content:
                        if not msg_content.strip().startswith("{") and \
                        not msg_content.strip().startswith("[System:"):
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": msg_content,
                            })

                if next_step == "vision_agent" or next_step == "decision_agent":
                    st.session_state.awaiting_human_review = True

                st.rerun()

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

# --- Human Review Panel ---
if st.session_state.awaiting_human_review and st.session_state.fraud_state:
    st.divider()
    st.subheader("🔍 Human Review Panel")
    st.warning("⚠️ This case requires human review before final decision.")

    fraud_state = st.session_state.fraud_state
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📋 Complaint Details**")
        st.write(f"**User ID:** {get_field(fraud_state, 'user_id')}")
        st.write(f"**Order ID:** {get_field(fraud_state, 'order_id')}")
        st.write(f"**Claimed Issue:** {get_field(fraud_state, 'claimed_issue')}")
        st.write(f"**Food Claimed:** {get_field(fraud_state, 'food_claimed')}")
        st.write(f"**Foreign Object:** {get_field(fraud_state, 'foreign_object')}")

    with col2:
        st.markdown("**🔬 Analysis Signals**")
        st.write(f"**Food Detected:** {get_field(fraud_state, 'food_detected')}")
        st.write(f"**Manipulation Risk:** {get_field(fraud_state, 'manipulation_risk')}")
        st.write(f"**Vision Confidence:** {get_field(fraud_state, 'vision_confidence')}")
        st.write(f"**Refund Ratio (30d):** {get_field(fraud_state, 'refund_ratio_30days')}")
        st.write(f"**Refunds (30d):** {get_field(fraud_state, 'refund_count_30days')}")
        st.divider()
        st.markdown("**👁️ What Gemini Saw**")
        st.info(get_field(fraud_state, 'seen_from_image') or "No visual analysis available")

    if st.session_state.image_path:
        st.image(st.session_state.image_path, caption="Complaint Image", width=300)

    col3, col4 = st.columns(2)
    with col3:
        if st.button("✅ Approve Refund", type="primary"):
            result = resume_graph()
            st.session_state.awaiting_human_review = False
            st.session_state.final_result = result
            st.rerun()
    with col4:
        if st.button("❌ Reject Refund", type="secondary"):
            result = resume_graph()
            st.session_state.awaiting_human_review = False
            st.session_state.final_result = result
            st.rerun()

# --- Final Result ---
if st.session_state.final_result:
    st.divider()
    st.subheader("📊 Final Decision")

    result = st.session_state.final_result
    decision = get_field(result, "final_decision")

    if decision == "APPROVE":
        st.success("✅ **APPROVED** — Refund will be processed")
    elif decision == "REJECT":
        st.error("❌ **REJECTED** — Complaint appears fraudulent")
    elif decision == "ESCALATE":
        st.warning("⚠️ **ESCALATED** — Sent to senior review team")
    elif decision == "ASK_MORE_EVIDENCE":
        st.info("📎 **MORE EVIDENCE NEEDED** — Please provide additional proof")

    st.markdown(f"**Reason:** {get_field(result, 'reason_for_decision')}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Fraud Risk Score", f"{get_field(result, 'fraud_risk_score', 0):.0%}")
    with col2:
        st.metric("Claim Confidence", f"{get_field(result, 'claim_confidence', 0):.0%}")
    with col3:
        st.metric("Decision Confidence", f"{get_field(result, 'decision_confidence', 0):.0%}")

    st.markdown("**🤖 HuggingFace AI Detection**")

    manipulation = get_field(fraud_state, 'manipulation_risk')
    if manipulation == "high":
        st.error(f"Manipulation Risk: {manipulation}")
    elif manipulation == "medium":
        st.warning(f"Manipulation Risk: {manipulation}")
    else:
        st.success(f"Manipulation Risk: {manipulation}")

# --- Chat Input ---
if not st.session_state.awaiting_human_review and not st.session_state.final_result:
    user_input = st.chat_input("Describe your complaint...")

    if user_input:
        if not st.session_state.messages or \
                st.session_state.messages[-1]["content"] != user_input:
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
            })

        with st.chat_message("user"):
            st.write(user_input)

        with st.spinner("Analyzing..."):
            try:
                result = run_graph_turn(
                    user_message=user_input,
                    image_path=st.session_state.image_path,
                )

                next_step = get_field(result, "next_step")
                messages = get_field(result, "messages") or []

                
                if messages:
                    last = messages[-1]
                    if isinstance(last, dict):
                        msg_type = last.get("type")
                        msg_content = last.get("content", "")
                    else:
                        msg_type = getattr(last, "type", "")
                        msg_content = getattr(last, "content", "")

                    if msg_type == "ai" and msg_content:
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": msg_content,
                        })
                        with st.chat_message("assistant"):
                            st.write(msg_content)

                
                if next_step == "vision_agent" or next_step == "decision_agent":
                    st.session_state.awaiting_human_review = True
                    st.rerun()
                elif next_step == "end":
                    st.session_state.final_result = result
                    st.rerun()

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")