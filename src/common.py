"""Shared helpers. Everything here is deterministic and needs no network."""
import glob, os, re
import pandas as pd

# Policy s5: two teams were renamed on 15 Jan 2026. Test set is all after that date -> use the NEW names.
RENAME = {"Installations": "Installs & Demo", "Consumables": "Filters & Consumables"}
TEAMS = ["Billing", "Filters & Consumables", "Installs & Demo", "Product Advice", "Repairs",
         "Returns & Replacement", "Warranty Claims"]
THRESHOLD = 0.60   # below this the service says "ask the customer a question" instead of guessing

def find(data_dir, name):
    hits = glob.glob(os.path.join(data_dir, f"*{name}"))
    if not hits:
        raise FileNotFoundError(f"No file ending in '{name}' under '{data_dir}'. Put the pack's CSVs there.")
    return hits[0]

def load(data_dir, name, **kw):
    return pd.read_csv(find(data_dir, name), **kw)

def clean_text(s):
    """Old Zoho rows contain mojibake (e.g. 'Ã¢â‚¬Â¦'): drop non-ASCII, lower-case, strip ids that carry no meaning."""
    s = re.sub(r"[^\x00-\x7f]+", " ", str(s)).lower()
    s = re.sub(r"\breg no sr\d+\b", " ", s)
    s = re.sub(r"\b(sr|ko)\d+\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def build_text(text, channel, product, warranty):
    """Message words plus three metadata tokens (channel, product, warranty) so one readable model sees everything."""
    return (clean_text(text) + " ch_" + str(channel).lower() + " pf_" + str(product).lower().replace(" ", "_")
            + " ws_" + str(warranty).lower())

def build_text_df(df):
    return [build_text(a, b, c, d) for a, b, c, d in zip(df.request_text, df.channel, df.product_family, df.warranty_status)]

PAID_RX = re.compile(r"\bpaid\b|payment|paying|already paid")
BILLING_PROBLEM_RX = re.compile(r"invoice|gst|charged twice|double charge|refund|emi|coupon|debited")
