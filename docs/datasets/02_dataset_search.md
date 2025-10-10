# 🔍 Finding NanoAOD Datasets in CMS

The **NanoAOD** (Nano Analysis Object Data) format is a lightweight, analysis-ready version of CMS data.  
It stores high-level physics objects such as electrons, muons, jets, and MET, making it ideal for user-level analysis.

To obtain NanoAOD samples, use the **CMS Data Aggregation System (DAS)** — the official metadata service to search and locate datasets and files.

---

## 🌐 CMS DAS (Data Aggregation System)

- **Web interface:**  
  👉 [https://cmsweb.cern.ch/das/](https://cmsweb.cern.ch/das/)

DAS allows you to:
- Search for **data** and **MC** samples by dataset name, primary dataset, or run number.  
- Explore dataset metadata: number of events, files, size, creation date, and storage sites.  
- Copy XRootD file paths for remote access.

> ⚠️ **Important:**  
> Accessing the DAS web interface requires a **valid grid certificate** installed in your web browser.  
> Without it, you may see a “Connection refused” or “Access denied” error.  
>  
> To install your certificate:
> 1. Obtain a valid **grid user certificate** (e.g., from CERN or your national grid authority).  
> 2. Import it into your browser (e.g., Firefox or Chrome).  
> 3. Ensure your browser trusts the CA (Certificate Authority) chain.  
>  
> More info: [CERN Certificate Guide](https://ca.cern.ch/ca/)

---

## 🧠 Example DAS Queries

Search for a specific dataset:
```bash
dataset=/DYJetsToLL_M-50_TuneCP5_13TeV-madgraphMLM-pythia8/RunIIFall18NanoAODv7/NANOAODSIM


