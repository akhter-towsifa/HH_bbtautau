#pragma once

#include <cmath>
#include <iostream>

#include <ROOT/RVec.hxx>
#include <TLorentzVector.h>

// Gen-level (LHE) di-Higgs kinematics: m_HH, pT_HH, cos(theta*). Only
// meaningful for HH signal samples (LHEPart_pdgId contains exactly two
// Higgs bosons, pdgId==25) -- callers should gate these on isSignal.

inline TLorentzVector GetDiHiggsP4LHE(const ROOT::RVec<float>& LHEPart_pt,
                                       const ROOT::RVec<float>& LHEPart_eta,
                                       const ROOT::RVec<float>& LHEPart_phi,
                                       const ROOT::RVec<float>& LHEPart_mass,
                                       const ROOT::RVec<int>& LHEPart_pdgId) {
    TLorentzVector dihiggs_p4(0., 0., 0., 0.);
    ROOT::RVec<TLorentzVector> higgs_p4s;
    TLorentzVector tmp_vec(0., 0., 0., 0.);
    for (size_t i = 0; i < LHEPart_pt.size(); ++i) {
        tmp_vec.SetPtEtaPhiM(0., 0., 0., 0.);
        if (std::abs(LHEPart_pdgId[i]) == 25) {
            tmp_vec.SetPtEtaPhiM(LHEPart_pt[i], LHEPart_eta[i], LHEPart_phi[i], LHEPart_mass[i]);
            higgs_p4s.push_back(tmp_vec);
        }
    }
    if (higgs_p4s.size() == 2) {
        dihiggs_p4 = higgs_p4s[0] + higgs_p4s[1];
    } else {
        std::cout << "Warning: Found " << higgs_p4s.size() << " Higgs bosons instead of 2." << std::endl;
        dihiggs_p4 = TLorentzVector(0., 0., 0., 0.);
    }
    return dihiggs_p4;
}

inline float GetMhhLHE(const ROOT::RVec<float>& LHEPart_pt, const ROOT::RVec<float>& LHEPart_eta,
                        const ROOT::RVec<float>& LHEPart_phi, const ROOT::RVec<float>& LHEPart_mass,
                        const ROOT::RVec<int>& LHEPart_pdgId) {
    auto dihiggs_p4 = GetDiHiggsP4LHE(LHEPart_pt, LHEPart_eta, LHEPart_phi, LHEPart_mass, LHEPart_pdgId);
    return static_cast<float>(dihiggs_p4.M());
}

inline float GetPthhLHE(const ROOT::RVec<float>& LHEPart_pt, const ROOT::RVec<float>& LHEPart_eta,
                         const ROOT::RVec<float>& LHEPart_phi, const ROOT::RVec<float>& LHEPart_mass,
                         const ROOT::RVec<int>& LHEPart_pdgId) {
    auto dihiggs_p4 = GetDiHiggsP4LHE(LHEPart_pt, LHEPart_eta, LHEPart_phi, LHEPart_mass, LHEPart_pdgId);
    return static_cast<float>(dihiggs_p4.Pt());
}

inline float GetCosThetaStarLHE(const ROOT::RVec<float>& LHEPart_pt, const ROOT::RVec<float>& LHEPart_eta,
                                 const ROOT::RVec<float>& LHEPart_phi, const ROOT::RVec<float>& LHEPart_mass,
                                 const ROOT::RVec<int>& LHEPart_pdgId) {
    ROOT::RVec<TLorentzVector> higgs_p4s;
    TLorentzVector tmp_vec(0., 0., 0., 0.);
    for (size_t i = 0; i < LHEPart_pt.size(); ++i) {
        tmp_vec.SetPtEtaPhiM(0., 0., 0., 0.);
        if (std::abs(LHEPart_pdgId[i]) == 25) {
            tmp_vec.SetPtEtaPhiM(LHEPart_pt[i], LHEPart_eta[i], LHEPart_phi[i], LHEPart_mass[i]);
            higgs_p4s.push_back(tmp_vec);
        }
    }
    if (higgs_p4s.size() != 2)
        return -2.f;  // invalid value
    TLorentzVector dihiggs_p4 = higgs_p4s[0] + higgs_p4s[1];
    TVector3 boost_vector = dihiggs_p4.BoostVector();
    TLorentzVector higgs1_boosted = higgs_p4s[0];
    higgs1_boosted.Boost(-boost_vector);
    return static_cast<float>(std::cos(higgs1_boosted.Theta()));
}
