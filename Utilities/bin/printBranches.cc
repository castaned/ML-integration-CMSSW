//getListOfBranches

#include "TFile.h"
#include "TTree.h"
#include <vector>
#include "TH1F.h"
#include "TPad.h"
#include "TCanvas.h"
#include "TROOT.h"

int main(int argc, char *argv[]) {

    if (argc < 3)
        return -1;
    TString samplefile = argv[1];
    TString outdir = argv[2];

    TFile* f = new TFile(samplefile, "READ");
    if (!f)
        return -2;
    TTree* t = (TTree*) f->Get("Events");

    if (!t)
        return -3;

    std::vector<TString> allbranches;
    auto tl = t->GetListOfBranches();
    for (int i=0; i<tl->GetEntries(); ++i){
      allbranches.push_back(tl->At(i)->GetName());
    }

    TCanvas cv;
    for (const auto& b : allbranches) {
        t->SetLineColor(kBlack);
        t->Draw(b + ">>" + b + "Light", "fj_isLight",
                "normalized");
        TH1F *histo = (TH1F*) gROOT->FindObject(b + "Light");
        histo->Draw("hist");

        t->SetLineColor(kAzure+6);
        t->Draw(b + ">>" + b + "Top", "fj_isTop", "same,normalized");
        histo = (TH1F*) gROOT->FindObject(b + "Top");
        histo->Draw("hist,same");

        t->SetLineColor(kSpring-8);
        t->Draw(b + ">>" + b + "W", "fj_isW", "same,normalized");
        histo = (TH1F*) gROOT->FindObject(b + "W");
        histo->Draw("hist,same");

        t->SetLineColor(kRed-9);
        t->Draw(b + ">>" + b + "Z", "fj_isZ", "same,normalized");
        histo = (TH1F*) gROOT->FindObject(b + "Z");
        histo->Draw("hist,same");

        t->SetLineColor(kViolet+2);
        t->Draw(b + ">>" + b + "H", "fj_isH", "same,normalized");
        histo = (TH1F*) gROOT->FindObject(b + "H");
        histo->Draw("hist,same");

        cv.Print(outdir + "/" + b + ".pdf");
    }

    return 0;

}
