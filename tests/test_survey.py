"""Hand-calculated design variance, covariance, replication and multiplicity checks."""
import unittest
import numpy as np
import pandas as pd
from gpdgc.survey import Design, difference, adjust_holm


class SurveyTests(unittest.TestCase):
    def setUp(self):
        self.frame=pd.DataFrame({'s':['a','a','b','b'],'p':['1','2','1','2'],'w':[1.]*4})

    def test_hand_calculated_stratified_variance(self):
        design=Design(self.frame,'w','s','p')
        estimate=design.mean([0,2,4,6])
        self.assertEqual(estimate['estimacion'],3)
        self.assertAlmostEqual(estimate['error_estandar']**2,.5)
        domain=design.mean([0,2,4,6],[True,False,True,False])
        self.assertAlmostEqual(domain['error_estandar']**2,2)

    def test_excluded_psus_remain_in_domain_variance(self):
        f=self.frame.iloc[[0,2]].copy()
        f.attrs['design_units']=list(self.frame[['s','p']].itertuples(index=False,name=None))
        e=Design(f,'w','s','p').mean([0,4])
        self.assertEqual(e['gl_diseno'],2)
        self.assertAlmostEqual(e['error_estandar']**2,2)

    def test_age_difference_preserves_shared_psu_covariance(self):
        f=pd.DataFrame({'s':['a']*4+['b']*4,'p':['1','1','2','2']*2,'w':[1.]*8})
        d=Design(f,'w','s','p'); young=np.arange(8)%2==0
        a=d.mean([0,2,2,4,4,6,6,8],young)
        b=d.mean([0,2,2,4,4,6,6,8],~young)
        self.assertAlmostEqual(difference(a,b)['estimacion'],-2)
        self.assertAlmostEqual(difference(a,b)['error_estandar'],0)
        self.assertGreater(difference(a,b,independent=True)['error_estandar'],0)

    def test_ratio_of_totals_and_mean_of_ratios_differ(self):
        d=Design(self.frame,'w','s','p')
        self.assertNotAlmostEqual(d.ratio([1,9,1,9],[2,10,2,10])['estimacion'],
                                 d.mean(np.array([1,9,1,9])/[2,10,2,10])['estimacion'])

    def test_bootstrap_uses_psus_and_shared_replicates(self):
        d=Design(self.frame,'w','s','p',replicates=999,seed=7)
        m=d.multipliers()
        np.testing.assert_allclose(m[:,:2].sum(axis=1),2)
        np.testing.assert_allclose(m[:,2:].sum(axis=1),2)
        e=d.distribution([1,2,3,4])['mediana']
        self.assertEqual(e['estimacion'],2)
        self.assertEqual(difference(e,e)['error_estandar'],0)
        other=Design(self.frame,'w','s','p',replicates=999,seed=7)
        np.testing.assert_array_equal(m,other.multipliers())

    def test_concentration_equal_values_and_exact_top_fraction(self):
        e=Design(self.frame,'w','s','p',replicates=99).distribution([2]*4,concentration=True,curve=True)
        self.assertAlmostEqual(e['gini']['estimacion'],0)
        self.assertAlmostEqual(e['top10']['estimacion'],.1)
        self.assertAlmostEqual(e['lorenz_30']['estimacion'],.3)

    def test_holm_known_values_and_separate_families(self):
        r=adjust_holm(pd.DataFrame({'familia':['a','a','a','b'],'p_valor':[.01,.04,.03,.04]}))
        np.testing.assert_allclose(r.p_ajustada_holm,[.03,.06,.06,.04])
        self.assertEqual(r.significativa_holm_005.tolist(),[True,False,False,True])

    def test_singleton_is_not_silently_treated_as_independent_households(self):
        with self.assertRaises(ValueError):Design(self.frame.iloc[:1],'w','s','p')
