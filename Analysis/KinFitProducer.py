import AnaProd.LegacyVariables as LegacyVariables


class KinFitProducer:
    """Computes the HHKinFit2-based kinematic fit (kinFit_m/kinFit_chi2/
    kinFit_convergence) once per dataset as an AnalysisCacheTask payload,
    instead of recomputing it inline inside every AnalysisCacheTask producer
    and HistTupleProducerTask run (see Analysis/hh_bbtautau.py's former
    defineKinFit(), now removed -- this is that logic, relocated verbatim).

    All real work happens in prepare_dfw() at the RDataFrame level; run() is
    a pass-through since LegacyVariables.GetKinFit() already defines columns
    natively named kinFit_m/kinFit_chi2/kinFit_convergence, matching exactly
    what payload_name="kinFit" + columns=[m, chi2, convergence] expects as
    this producer's final output names.
    """

    def __init__(self, cfg, payload_name, period):
        self.payload_name = payload_name
        self.period = period
        if not LegacyVariables.initialized:
            LegacyVariables.Initialize(load_kinfit=True, load_svfit=False, load_mt2=False)

    def prepare_dfw(self, dfw, dataset):
        if "entry_valid" not in dfw.df.GetColumnNames():
            dfw.df = dfw.df.Define("entry_valid", "Hbb_isValid")
        dfw.df, _ = LegacyVariables.GetKinFit(dfw.df)
        self.vars_to_save = ["kinFit_m", "kinFit_chi2", "kinFit_convergence"]
        return dfw

    def run(self, array):
        return array
