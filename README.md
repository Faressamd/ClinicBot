CLINIC-BOT (Zephyr) - Ready to run (French UI)

Contents:
- app.py : Streamlit app (FR)
- clinical_case_generator.py : HF router call
- .streamlit/secrets.toml : contains HF_TOKEN placeholder and MODEL (you must add your token)
- requirements.txt

How to run:
1. (Optional) Create and activate a virtual environment:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # PowerShell on Windows
2. Install requirements:
   pip install -r requirements.txt
3. Place your Hugging Face token in .streamlit/secrets.toml:
   HF_TOKEN = "hf_your_token_here"
   MODEL = "HuggingFaceH4/zephyr-7b-beta"
4. Run the app:
   streamlit run app.py

Notes:
- Use a READ token with Inference access in your Hugging Face account settings.
- Model responses can take 10-40 seconds.
- Validate clinically any generated content before using it for teaching.
