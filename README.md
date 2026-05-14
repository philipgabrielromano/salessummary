# 📈 Power BI PDF Summarizer

Automatically generates AI-powered executive summaries from your daily Power BI report emails and delivers them as beautiful HTML emails to your leadership team.

## Architecture

```
┌──────────────────┐     ┌────────────────────┐     ┌──────────────────┐
│  Microsoft 365   │     │   Python App        │     │   OpenAI GPT-4o  │
│  Outlook Inbox   │────▶│   (Render Cron)     │────▶│   Summarization  │
│                  │     │                     │     │                  │
│  Power BI Email  │     │  1. Fetch email     │     │  Structured JSON │
│  + PDF Attach.   │     │  2. Extract PDF     │     │  with KPI status │
└──────────────────┘     │  3. Call OpenAI     │     └──────────────────┘
                         │  4. Render HTML     │
                         │  5. Send email      │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌──────────────────┐
                         │  Leadership Team  │
                         │  HTML Email with  │
                         │  🟢🟡🔴 Status   │
                         └──────────────────┘
```

## Features

- 🔍 **Smart email detection** — Finds the latest Power BI report by subject/sender filter
- 📄 **Table-aware PDF parsing** — Extracts structured tables and numbers using pdfplumber
- 🤖 **AI-powered analysis** — GPT-4o identifies KPIs, trends, risks, and action items
- 🎨 **Professional HTML emails** — Outlook-compatible, mobile-responsive design
- 🚦 **Status indicators** — Red/Yellow/Green for instant visual assessment
- ⏰ **Scheduled execution** — Runs automatically on Render's free tier cron

## Quick Start

### Prerequisites
- Python 3.11+
- Microsoft 365 account with admin access to Azure AD
- OpenAI API key
- Render account (free tier works)

### 1. Clone and Install

```bash
git clone https://github.com/your-org/power-bi-summarizer.git
cd power-bi-summarizer
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up Azure AD App (see detailed guide below)

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 4. Test Locally

```bash
python main.py
```

### 5. Deploy to Render

Push to GitHub, then connect the repo in Render (see deployment section below).

---

## 🔐 Azure AD App Registration (Step-by-Step)

This app uses **application permissions** (no user login required) to read email and send on behalf of a mailbox.

### Step 1: Register the App

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Microsoft Entra ID** → **App registrations**
3. Click **+ New registration**
4. Fill in:
   - **Name:** `Power BI Summarizer`
   - **Supported account types:** "Accounts in this organizational directory only"
   - **Redirect URI:** Leave blank
5. Click **Register**
6. Copy the **Application (client) ID** → this is your `AZURE_CLIENT_ID`
7. Copy the **Directory (tenant) ID** → this is your `AZURE_TENANT_ID`

### Step 2: Create a Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **+ New client secret**
3. Description: `Power BI Summarizer Production`
4. Expiration: Choose 24 months (set a calendar reminder to rotate!)
5. Click **Add**
6. **IMMEDIATELY copy the Value** → this is your `AZURE_CLIENT_SECRET`
   - ⚠️ You can only see this once!

### Step 3: Add API Permissions

1. Go to **API permissions** → **+ Add a permission**
2. Select **Microsoft Graph** → **Application permissions**
3. Add these permissions:
   - `Mail.Read` — Read mail in all mailboxes
   - `Mail.Send` — Send mail as any user
4. Click **Add permissions**
5. Click **✅ Grant admin consent for [Your Org]**
   - You need Global Admin or Privileged Role Admin to do this

### Step 4: (Optional) Restrict Mailbox Access

For security, you can limit the app to only access specific mailboxes using an **Application Access Policy**:

```powershell
# Connect to Exchange Online PowerShell
Connect-ExchangeOnline

# Create a mail-enabled security group and add your mailbox
New-DistributionGroup -Name "Power BI Summarizer Access" -Type Security

# Create the access policy
New-ApplicationAccessPolicy `
    -AppId "YOUR_CLIENT_ID" `
    -PolicyScopeGroupId "Power BI Summarizer Access" `
    -AccessRight RestrictAccess `
    -Description "Restrict Power BI Summarizer to specific mailboxes"
```

---

## ⚙️ Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `AZURE_TENANT_ID` | ✅ | Azure AD tenant ID | `12345678-abcd-...` |
| `AZURE_CLIENT_ID` | ✅ | App registration client ID | `87654321-dcba-...` |
| `AZURE_CLIENT_SECRET` | ✅ | App client secret value | `abc~123...` |
| `MAILBOX_USER` | ✅ | Email address to read from | `reports@company.com` |
| `EMAIL_SUBJECT_FILTER` | ❌ | Subject line filter | `Power BI` (default) |
| `EMAIL_SENDER_FILTER` | ❌ | Sender email filter | `no-reply@powerbi.com` |
| `RECIPIENT_EMAILS` | ✅ | Comma-separated recipients | `ceo@co.com,cfo@co.com` |
| `OPENAI_API_KEY` | ✅ | OpenAI API key | `sk-...` |
| `OPENAI_MODEL` | ❌ | Model to use | `gpt-4o` (default) |
| `COMPANY_NAME` | ❌ | Your company name | `Acme Corp` |
| `REPORT_NAME` | ❌ | Report display name | `Daily Performance Report` |
| `FULL_REPORT_URL` | ❌ | Link to Power BI online | `https://app.powerbi.com/...` |
| `LOG_LEVEL` | ❌ | Logging verbosity | `INFO` (default) |

---

## 🚀 Deploy to Render

### Option A: Blueprint (Recommended)

1. Push this repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** → **Blueprint**
4. Connect your GitHub repo
5. Render detects `render.yaml` automatically
6. Add your environment variables (marked `sync: false` will prompt you)
7. Deploy!

### Option B: Manual Cron Job

1. Go to Render Dashboard → **New** → **Cron Job**
2. Connect your GitHub repo
3. Configure:
   - **Name:** `power-bi-summarizer`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Schedule:** `30 13 * * 1-5` (8:30 AM EST, weekdays)
4. Add all environment variables in the **Environment** tab
5. Click **Create Cron Job**

### Adjusting the Schedule

The cron expression in `render.yaml` is set to `30 13 * * 1-5`:
- `30` — minute 30
- `13` — 1 PM UTC (= 8:30 AM EST / 9:30 AM EDT)
- `*` — every day of month
- `*` — every month
- `1-5` — Monday through Friday

**Adjust for your timezone and when your Power BI report arrives.** Make sure the cron runs ~30 minutes AFTER the Power BI email typically arrives.

---

## 🧪 Local Development & Testing

### Run Locally

```bash
# Activate virtual environment
source .venv/bin/activate

# Load environment variables
export $(cat .env | xargs)

# Run the pipeline
python main.py
```

### Test Individual Components

```python
# Test PDF extraction
from pdf_extractor import extract_pdf_content
from pathlib import Path
content = extract_pdf_content(Path("sample_report.pdf"))
print(content[:1000])

# Test summarization (requires OpenAI key)
from summarizer import generate_summary
from config import Config
config = Config.from_env()
summary = generate_summary(content, config)
print(summary)

# Test email rendering
from email_template import render_email
html = render_email(summary, "Test Report", "Test Co")
Path("test_email.html").write_text(html)
# Open test_email.html in browser to preview
```

---

## 🔧 Troubleshooting

### "No Power BI report email found"
- Check that `EMAIL_SUBJECT_FILTER` matches your actual email subject
- Verify `MAILBOX_USER` is the correct mailbox
- Ensure the app has `Mail.Read` permission with admin consent
- Check if an Application Access Policy is restricting access

### "401 Unauthorized" from Graph API
- Verify your `AZURE_CLIENT_SECRET` hasn't expired
- Confirm admin consent was granted for permissions
- Check that `AZURE_TENANT_ID` is correct

### "No PDF attachment found"
- The app looks for files with `.pdf` extension or `application/pdf` content type
- Check if your Power BI email uses a different attachment format

### "No content extracted from PDF"
- If your PDF is image-based (scanned), pdfplumber can't extract text
- Power BI PDFs are typically text-based, so this is rare
- Consider adding OCR (pytesseract) if needed

### Empty or poor-quality summaries
- Set `LOG_LEVEL=DEBUG` to see the raw extracted content
- If tables aren't extracting well, check the PDF structure
- Try adjusting the prompt in `summarizer.py`

### Email not rendering correctly
- The template uses inline CSS for Outlook compatibility
- Test with [Litmus](https://litmus.com) or [Email on Acid](https://emailonacid.com)
- Avoid adding external CSS — Outlook strips `<style>` tags

---

## 📁 Project Structure

```
power-bi-summarizer/
├── main.py              # Entry point — orchestrates the pipeline
├── config.py            # Environment variable configuration
├── graph_client.py      # Microsoft Graph API (email read/send)
├── pdf_extractor.py     # PDF table & text extraction
├── summarizer.py        # OpenAI GPT-4o summarization
├── email_template.py    # HTML email rendering
├── requirements.txt     # Python dependencies
├── render.yaml          # Render cron job config
├── .env.example         # Environment variable template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

---

## 🔄 Maintenance

- **Rotate client secret** before it expires (set a calendar reminder)
- **Monitor OpenAI costs** — each run uses ~2K-5K tokens ($0.01-0.03)
- **Check Render logs** if emails stop arriving
- **Update the prompt** in `summarizer.py` if your report format changes

---

## License

MIT — Use freely for your organization.
