import re
import streamlit as st
from transformers import pipeline

# ---------------- CONFIG ----------------
# Load models
pipe1 = pipeline("text-classification", model="ElSlay/BERT-Phishing-Email-Model")
pipe2 = pipeline("text-classification", model="Eason918/malicious-url-detector")
pipe3 = pipeline("text-classification", model="r3ddkahili/final-complete-malicious-url-model")

# Label normalization
def normalize_label(label):
    return "benign" if label == "LABEL_0" else "malicious"

# Weighted Ensemble Calculation (only pipeline2 and 3)
def calculate_weighted_prediction(label2, score2, label3, score3):
    weights = {"Pipeline2": 0.3, "Pipeline3": 0.7}
    score_dict = {"benign": 0.0, "malicious": 0.0}
    score_dict[normalize_label(label2)] += weights["Pipeline2"] * score2
    score_dict[normalize_label(label3)] += weights["Pipeline3"] * score3
    final_label = max(score_dict, key=score_dict.get)
    final_score = score_dict[final_label]
    return final_label, final_score

# Extract URLs
def extract_urls(text):
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    return re.findall(url_pattern, text)

# ---------------- UI START ----------------
st.set_page_config(page_title="📩 Email Malicious Detector", layout="wide")
st.markdown("<h1 style='text-align: center;'>📩 Malicious Email Detection App</h1>", unsafe_allow_html=True)

st.markdown("### ✉️ Enter your email content:")
email_text = st.text_area("Paste your email content here:", height=200)

if st.button("🚨 Scan Email & Analyze URL"):
    if not email_text.strip():
        st.warning("⚠️ Please input some email content.")
    else:
        result1 = pipe1(email_text)[0]
        label1, score1 = result1['label'], result1['score']
        pred1 = normalize_label(label1)

        if pred1 == "benign":
            st.markdown("## 🛡️ **Prediction Result:**")
            st.success(f"✅ BENIGN EMAIL CONTENT (Confidence Score: {score1:.2%})")
        else:
            urls = extract_urls(email_text)
            if not urls:
                st.warning("⚠️ Email content is malicious, but no URL found for further analysis.")
            else:
                url = urls[0]
                result2 = pipe2(url)[0]
                result3 = pipe3(url)[0]
                label2, score2 = result2['label'], result2['score']
                label3, score3 = result3['label'], result3['score']

                final_label, final_score = calculate_weighted_prediction(label2, score2, label3, score3)

                st.markdown("## 🛡️ **Prediction Result:**")
                if final_score < 0.6:
                    st.warning(f"🤔 URLs in email content are UNCERTAIN - Confidence too low ({final_score:.2%}). Please review manually.")
                elif final_label == "benign":
                    st.success(f"✅ URLs in email content are BENIGN (Confidence Score: {final_score:.2%})")
                else:
                    st.error(f"⚠️ URLs in email content are MALICIOUS (Confidence Score: {final_score:.2%})")
