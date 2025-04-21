import os

era = "ERA_string"
ver = "your_version"
indir = f"/eos/user/u/username/HH_bbtautau_Run3/histograms/{ver}/{era}/merged/"
plotdir = f"/eos/user/t/toakhter/HH_bbtautau_Run3/histograms/{ver}/{era}/plots/"

varnames = ["tau1_pt", "tau2_pt", "b1_pt", "b2_pt", "tautau_m_vis", "bb_m_vis", "MT2"] #"bbtautau_mass"

channellist = ["eE", "eMu", "muMu", "eTau", "muTau", "tauTau"]

cat = "inclusive"

using_uncertainties = True #When we turn on Up/Down, the file storage changes due to renameHists.py

for var in varnames:
    for channel in channellist:
        filename = os.path.join(indir, var, f"{var}.root")
        print("Loading fname ", filename)
        os.makedirs(plotdir, exist_ok=True)
        outname = os.path.join(plotdir, f"HHbbtautau_{channel}_{var}_StackPlot.pdf")

        if not using_uncertainties:
            os.system(f"python3 ../FLAF/Analysis/HistPlotter.py --inFile {filename} --bckgConfig ../config/background_samples.yaml --globalConfig ../config/global.yaml --outFile {outname} --var {var} --category {cat} --channel {channel} --uncSource Central --wantData --year {era} --wantQCD False --rebin False --analysis HH_bbtautau --qcdregion OS_Iso --sigConfig ../config/{era}/samples.yaml --wantSignals")

        else:
            filename = os.path.join(indir, var, 'tmp', f"all_histograms_{var}_hadded.root")
            os.system(f"python3 ../FLAF/Analysis/HistPlotter.py --inFile {filename} --bckgConfig ../config/background_samples.yaml --globalConfig ../config/global.yaml --outFile {outname} --var {var} --category {cat} --channel {channel} --uncSource Central --wantData --year {era} --wantQCD False --rebin False --analysis HH_bbtautau --qcdregion OS_Iso --sigConfig ../config/{era}/samples.yaml --wantSignals")