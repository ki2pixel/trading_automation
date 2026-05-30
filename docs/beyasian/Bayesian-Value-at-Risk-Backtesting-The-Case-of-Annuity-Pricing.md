

Munich Personal RePEc Archive

# **Bayesian Value-at-Risk Backtesting: The Case of Annuity Pricing**

Leung, Melvern and Li, Youwei and Pantelous, Athanasios and Vigne, Samuel

Monash Business School, Monash University, Australia, Hull University Business School, University of Hull, U.K., Monash Business School, Monash University, Australia, Trinity Business School, They University of Dublin, Ireland

November 2019

Online at https://mpra.ub.uni-muenchen.de/101698/

MPRA Paper No. 101698, posted 19 Jul 2020 02:02 UTC

Bayesian Value-at-Risk Backtesting: The Case of Annuity Pricing

Melvern Leunga, Youwei Lib, Athanasios A. Pantelousa,∗, Samuel A. Vignec

*aDepartment of Econometrics and Business Statistics, Monash Business School, Monash University, Australia*  
*bHull University Business School, University of Hull, U.K.*  
*cTrinity Business School, They University of Dublin, Ireland*

Abstract

We propose a new Unconditional Coverage test for VaR-forecasts under a Bayesian framework that significantly minimise the direct and indirect effects of *p*\-hacking or other biased outcomes in decision-making, in general. Especially, after the global financial crisis of 2007-09, regulatory demands from Basel III and Solvency II have required a more strict assessment setting for the internal financial risk models. Here, we employ linear and nonlinear Bayesianised variants of two renowned mortality models to put the proposed backtesting technique into the context of annuity pricing. In this regard, we explore whether the stressed longevity scenarios are enough to capture the experiences liability over the foretasted time horizon. Most importantly, we conclude that our Bayesian decision theoretic framework quantitatively produce a strength of evidence favouring one decision over the other.  
*Keywords:* Bayesian decision theory; Value-at-Risk; Backtesting; Annuity pricing; Longevity risk

1. Introduction and Motivation

Over the past few decades, the popularity of *Value-at-Risk* (VaR) has increased significantly among practitioners for measuring and managing risk in the insurance and financial services in- dustries. However, a risk measure is only as good as it is able to accurately predict future risks accordingly, and thus, to measure its accuracy we need to develop effective backtest procedures. These processes should allow the possibility to validate a risk measure given its out-of-sample fore- casts and actual realized results (Christoffersen and Pelletier, 2004), such as those found using VaR.1 By definition, the VaR is the *q*\-quantile of a Profit/Loss distribution, and a backtesting

∗  
Corresponding author  
*Email addresses:* [Melvern.Leung@monash.edu](mailto:Melvern.Leung@monash.edu) (Melvern Leung), [Youwei.Li@hull.ac.uk](mailto:Youwei.Li@hull.ac.uk) (Youwei Li),  
[Athanasios.Pantelous@monash.edu](mailto:Athanasios.Pantelous@monash.edu) (Athanasios A. Pantelous ), [vignes@tcd.ie](mailto:vignes@tcd.ie) (Samuel A. Vigne)  
1While VaR is a widely used risk measure in finance, and in several decision-making processes in general, however other risk measures such as Stressed-trends and Expected Shortfall can also be backtested. The results presented in this study can be extended in several other directions, however we will address them in our future research.

*Preprint submitted to Elsevier	4th November 2019*

mechanism is to determine whether the required coverage *q* is indeed achieved. In practice, the idea of backtesting as explained by Kupiec (1995) is a type of “*reality check* ” to identify whether risk measurement models are able to accurately determine the risk exposures experienced.

After the global financial crisis of 2007-09, regulatory demands from Basel III and Solvency II have required a very strict assessment for internal financial risk models, respectively for banks and insurance companies (Drenovak et al., 2017). Kupiec (1995) was the pioneer of backtesting, whereby sequences of ones and zeros are determined by whether the risk-measure forecasts is able to capture the actual realized returns. A likelihood ratio test is then constructed to test if the proportion of ones and zeros correctly represents the required coverage. Although there has been a large emphasis on VaR forecasting in literature (e.g., Berkowitz and O’Brien, 2002, Glasserman et al., 2002, Christoffersen, 2009, Nieto and Ruiz, 2016), the backtesting literature has since gained traction after the development of the *Unconditional Coverage* (UC) backtest by Kupiec (1995), these include the works from Christoffersen (1998), Ziggel et al. (2014) and Wied et al. (2016).

With the recent developments of Bayesian statistical techniques, there is an increasing motion towards the use of a Bayesian decision framework in hypothesis testing. In particular, Harvey (2017) mentions the importance and how to implement a Bayesian test in concurrence of the standard *Null Hypothesis Significance Testing* (NHST), as means of comparisons between hypotheses. The issue as stated and convincingly discussed in the American Finance Association president’s address Harvey (2017) is that hypothesis testing, which is a significant tool used extensively in the finance literature, and its testing procedures are based on the critical assumption that the null hypothesis is true, and the alternative hypothesis is indirectly inferred. However, the idea of *p*\-value has caused some scepticism among researchers, since non-rejected null hypotheses can simply be removed after the testing procedure in order to obtain a significant result in for example regression analysis. This formed the basis of the idea of *p*\-hacking and biased outcomes as noted by Harvey (2017).

The Bayesian testing began when Berger and Sellke (1987) developed the idea of *Bayes Factor* (BF) to determine a ratio of evidence, and recently, this idea has been applied extensively in different scientific fields. Overall, the Bayesian test has many advantages in the realm of testing, it allows a measure of evidence towards one hypothesis in comparison to another using direct inference, and there is no arbitrary cut-off point. Most importantly, using Bayes rule, we are able to obtain the probability of a hypothesis being correct given the dataset. The idea behind a Bayesian backtesting framework is to alleviate the use of frequentist *p*\-values, and instead focus on the BF (or Posterior odds) which expresses conclusions based on a ratio rather than those expressed

indirectly via a confidence interval and *p*\-value. We can conduct inference using sampling properties of our posterior distribution rather than on large sample asymptotic approximations to the null distribution.

Our paper contributes to the literature in three distinctive ways. Firstly, we propose a new Bayesian framework for the UC VaR backtest. This framework allows for the inclusion of prior knowledge to be used in the decision making step which deviates from standard testing procedures under the frequentist framework. We first state the assumptions used by the UC test, then develop the Bayesian decision theoretic framework surrounding these assumptions. Further, the flexibility of the Bayesian framework can also be tailored to one-tail testing, as opposed to the two-tail tests presented in Kupiec (1995), this permits the capability to separately test whether the VaR- model underestimated or overestimated a required VaR-exceedance criteria. Most importantly, our Bayesian VaR backtesting framework developed in this study is highly flexible, and easy to implement due to the Bayesian conjugacy property which allows a closed-form expression of the posterior. What is more, in the case where Bayesian conjugacy does not exist, we employ recent econometric advancements in Bayesian estimation which also allows for numerical approximations such as *Monte-Carlo Markov Chain* (MCMC) methods. Furthermore, as a robustness test, varying prior distributions were used to ensure the decision is coherent among varying hyper-parameters.

Secondly, since 2016, Solvency II was established with the aim of ensuring insurance companies meet their obligations to policyholders (e.g., Eckert and Gatzert, 2018).2 The idea behind this notion is that the company is required to meet its obligation payments with a probability of 99.5% over 12 months (Hari et al., 2008). However, Pillar 1 allows room for internal models in terms of assessing the financial stability of the insurance company, they have the choice to either use the capital requirements laid by the supervisory regulators or keep capital reserves based on their own risk-based models. The supervisory regulator uses a mortality shock based model which has been criticized, see for instance, Plat (2011), for its over-estimation of longevity trend risk. Moreover, they apply risk measures such as VaR and also longevity-trend stress test scenarios in order to evaluate the solvency capital requirement. In the present paper, we employ the linear and nonlinear variants of the Lee and Carter (1992) (LC) and the Cairns et al. (2006) (CBD) model which are two renowned mortality models in the corresponding literature. Then, we develop Bayesian estimation methods for the mortality models utilizing the *Extended Kalman Filter* (EKF) and the MCMC

2This regulation contains three pillars, and our focus in this paper is on pillar 1, where it contains the risk based solvency capital requirements.

techniques.

Finally, we develop the idea of backtesting in annuity liabilities which has two main advan- tages (Leung et al., 2018). Firstly, the backtesting framework allows us to measure the ability for mortality models to capture longevity risk associated with annuity itself. Secondly, it allows the ability to determine models most suitable for longevity risk applications.3 Our focus is on the long term longevity trend risk, and in this case a longevity stress test scenarios would be most suitable. This mainly stems from the fact that longevity trend risk exacerbates over a longer period, and as such a one-year VaR would most likely be unsuitable. Thus, under a longevity stress trend scenario, it is crucial that a suitable backtesting method is developed to determine if the under- lying longevity risks associated with a pricing instrument are actually captured by the mortality model used. In essence, the backtesting procedure is determined by the outcome of whether the specified mortality model will be able to produce a forecast such that with probability of 99.5% obligated payments from an annuity can be met. Although our focus is on the immediate annuity with contingent payments based on the policyholders lifespan, we should emphasise here that the backtesting framework we develop can also be extended to measure accuracy of any type of risk measures.

The paper is organised as follows. Section 2 and Appendix A focus on developing the VaR Bayesian backtesting framework for the novel Unconditional Coverage test. Section 3 explains the estimation procedure of the Bayesian mortality models under a state-space representation setting. A particular interest is paid to the nonlinear dynamics when modelling (central) death rates rather than the crude mortality estimates. Section 4 and Appendices B and C (see also, the extensive SI provided) contain the empirical results of fitted LC and CBD model, as well the Bayesian forecast- ing method algorithms used in the paper. Section 5 applies the Bayesian backtesting framework developed to a 99.5% longevity stressed scenarios under an immediate annuity calculation. We determine clearly which model produces the most favourable results under a longevity stressed scenario implementing the Solvency II regulation. Finally, Section 6 concludes the paper.

2. A Bayesian Backtesting Tool

Financial risk model evaluation plays a major part in risk management, and typically this evaluation process is called *backtesting procedure*4 which tries to measure the accuracy of the risk

3More discussion about life annuities can be found in Supplementary Information (SI) Section 1\.  
4A good overview of backtesting and its procedures is given in Campbell (2007), see also Nieto and Ruiz (2016).

models promised coverage. For instance, a VaR model tries to define a conditional quantile (or coverage) of the return distribution. To evaluate the effectiveness of the VaR model, we can backtest it and determine whether the required coverage rate is met. This is usually accomplished by using ex-post returns on ex-ante VaR forecasts. In this Section, we propose a new UC backtest for VaR-forecasts under a Bayesian framework which is a cornerstone in this paper.

1. *The Bayesian Framework*

Before we proceed with the new UC backtest, let us consider two hypotheses, *H*0 and *H*1, we wish to test. Under the standard NHST framework, inference is normally conducted on *P* (*y*|*Hi*)*, i* \= 0*,* 1, however applying Bayes rule, we obtain the following relation,

*π*(*H* |*y*) \= *π*(*y*|*Hi*)*π*(*Hi*) *,*

*i	π*(*y*)

where *π*(*y*) is the marginalizing constant to ensure *P* (*Hi*|*y*) is a proper probability distribution, and finally the point of interest, the posterior odds ratio, is given by,

*π*(*H*0|*y*) \= *π*(*y*|*H*0)*π*(*H*0) \= BF	*π*(*H*0) *,*	(2.1)  
*π*(*H*1|*y*)	*π*(*y*|*H*1)*π*(*H*1)

01 *π*(*H*1)

where BF01 \= *π*(*y*|*H*0)

is commonly referred to as the BF, and *π*(*H*0)  
1

is known as the *prior odds*.

BF01 measures the change in evidence when going from the prior to posterior odds. In the decision making process where both hypotheses are given equal weighting, the testing framework focuses solely on BF01, thus a higher positive value for BF01 implies *π*(*H*0|*y*) *\> π*(*H*1|*y*), and concludes an  
increased support for *H*0.

Consider now a point null hypothesis {*H*0 \= *θ*0} and a composite alternative hypothesis {*H*1 /\=

*θ*0}. The Bayesian framework then assigns a prior distribution over both hypotheses. Let *y* :=

{*y*1*, ..., yn*} be a vector of *n* observations, the likelihood function of the observed data is given by *l*(*y*|*θ*), where *θ* is the parameter of interest. Then, for a given prior, *π*(*θ*), our posterior distribution is given by,  
*π*(*θ*|*y*) \= *l*(*y*|*θ*)*π*(*θ*) *.*	(2.2)  
*π*(*y*)

The prior specifications will be as follows: “*under H*0*, we assign the (point mass) prior π*(*θ*) \= *θ*0*, whereas for H*1*, we assign a prior distribution over the parameter space required* ”. The decision to accept *H*0 is denoted by “*a*0” and the decision against *H*0 is denoted by “*a*1”. Overall, for a given loss function, L\[*ai*; *θ*\]*, i* \= 0*,* 1, *H*0 is rejected when the expected posterior loss for *H*0 is sufficiently

larger than the expected posterior loss under *H*1. The expected posterior loss for the *ith* decision

is given by,

*Eπ*(*θ*|*y*) \[*L*(*θ, ai*)\] \=  
*θ*

and we will reject *H*0 when,

L\[*ai*; *θ*\]*π*(*θ*|*y*)*dθ,* for *i* \= 1*,* 2	(2.3)

(L\[*a*0; *θ*\] — L\[*a*1; *θ*\]) *π*(*θ*|*y*)*dθ \>* 0*.*	(2.4)  
*θ*

If we choose to employ a zero-one loss function5,

L\[*a* ; *θ*\] \= 0	if *θ* \= *θ*0*,*

(2.5)  
1	if *θ* /\= *θ*0*,*

with L\[*a*1; *θ*\] \= 1 — L\[*a*0; *θ*\]. Given equal probability of the *H*0 and *H*1 occurring, that is *π*(*H*0) \= *π*(*H*1) \= 0*.*5, we will have the following decisions to make. For the first decision, when *θ* \= *θ*0, we will accept *H*0 with decision *a*0, and the second decision, *a*1, occurs when *θ* /\= *θ*0. To tabulate the decision outcome more formally:

Choose: *a*0*,*	if *θ* \= *θ*0*,*  
*a*1*,*	if *θ* /\= *θ*0*.*

Combining Eqs. (2.3), (2.4) and (2.5), rejection of the *H*0 will occur when,

*θ* L\[*a*0; *θ*\]*π*(*θ*|*y*)*dθ	l*(*y*|*θ* \= *θ*0)  
∫	\= ∫

*\<* 1*,*	(2.6)

where the quantity

*l*(*y*|*θ*\=*θ*0)  
*θ l*(*y*|*θ*)*π*(*θ*)*dθ*

is the BF01.6 Further, note that the marginalizing constant *π*(*y*)

from Eq. (2.2) disappears in Eq. (2.6), since it appears in both the numerator and denominator. The *Bayesian* version of the *Likelihood Ratio Test* (BLRT) was pioneered by Li et al. (2014), where instead of having a 0 — 1 loss function which corresponds to BF01, they used a continuous loss

5A zero-one loss function is a commonly chosen loss function used in Bayesian hypothesis testing, this is simply due to its binary outcome, and is equivalent to either rejecting(*a*1) or accepting(*a*0) the null hypothesis.

6The range of values that BF01 can take represents different levels of evidence which supports the null or alternative hypothesis, in Table 1 of Goodman (2001) the strength of evidence against the null hypothesis for a given BF is shown.

difference function, defined by

∆L\[*H*0; *θ*\] \= —2 \[log(*π*(*y*|*θ*0)) — log(*π*(*y*|*θ*))\] *,*

under a continuous loss difference function, rejection of *H*0 occurs when

∆L\[*H*0; *θ*\]*π*(*θ*|*y*)*dθ \>* 0*,*  
*θ*

and the Bayesian test statistic is given by,

*T*BLRT(*y, θ*) \=  —2 ∫ \[log(*π*(*y*|*θ*0)) — log(*π*(*y*|*θ*))\] *π*(*θ*|*y*)*dθ* \+ 1*.*	(2.7)

The main difference between the BLRT and BF01 is that the BLRT focuses on averaging over the (log)posterior distribution, whereas BF01 averages over the prior distribution. Li et al. (2014) also found that *T*BLRT(*y, θ*) has an asymptotic *χ*2(1)-distribution, and a convenient property of the BLRT statistic is that if the integral in Eq. (2.7) has no analytical form, it can be approximated via an MCMC,

*M*  
*T*BLRT(*y, θ*) \= —2	log(*π*(*y*|*θ*0)) — log(*π*(*y*|*θi*))  */M* \+ 1*,*	(2.8)

*i*\=1

where *i* represents the *ith* MCMC draw, and *M* corresponds to the number of MCMC iterations.

In this case, we can produce Bayesianised *p*\-values via

*p* \= *P* (*χ*2(1) ≤ *T*BLRT)*.*

2. *A New Unconditional Coverage Backtest*

The statistical backtest for VaR developed by Kupiec (1995) tests whether a risk model truly generated the correct coverage using the LRT. In this section, we formulate a novel approach of the UC backtest using the Bayesian decision theoretic framework developed in the previous section.  
Let *y* denote the daily observed asset or portfolio return time series *yt* for *t* ∈ (1*, . . . , T* ), and

the VaR as *P* (*yt* ≥ *V aRt*|F*t*−1 (*p*)) \= *p*. To produce interval forecasts for each observation, we let

*Ut*|F*t*−1 (*p*) denote the lower forecast interval produced for time *t* using information up until *t* — 1

with coverage *p*. Let us define an indicator variable where,

I (*t*) \= 1*,*	if *yt* ∈ (—∞*, Ut*|F*t*−1 (*p*))

(2.9)  
0*,*	otherwise,

where F*t*−1 corresponds to the information set F*t*−1 := {I*p*(1)*, . . . ,* I*p*(*t* — 1\)}.

In laymen terms, if the observed daily return, *yt*, is not greater than the expected lower bound,

*yt \> Ut*|F*t*−1 (*p*), then we conclude that the VaR forecasts are violated at time *t* and we assign a value of 1\. Kupiec (1995) examines whether the average non-violations shown in Eq. (2.9) occurs at the required coverage *p*, mathematically,

*E* "(1*/T* ) Σ*t*\=1 I*p*(*t*)\# \= *P* (I*p*(*t*) \= 1\) \= *p,* ∀*t.*	(2.10)

This also implies that each I*p*(*t*) ∼ *Be*(*p*), where *Be*(*p*) represents the Bernoulli distribution with probability *p* success. Let I*p* := {I*p*(*t*) : *t* ∈ (1*, ..., T* )}, and let *m*1 and *m*0 denote the number of one and zero occurrences in I*p* respectively. Then I*p* will be a vector of size *T* \= *m*1 \+ *m*0. Our aim is to determine whether or not *E*\[I*p*(*t*)\] \= *p*∗, for some predetermined probability *p*∗ and since, I*p*(*t*) ∼ *Be*(*p*) ∀*t,* the joint likelihood function will be given by,

*l*(I|*p*) \= *pm*1 (1 — *p*)*m*0 *.*	(2.11)

The Bayesian framework starts by assigning priors on *p*. Under the *H*0 := *p* \= *p*∗ with an assigned point mass prior. Under the alternative *H*1 := *p* /\= *p*∗, since *p* has a support between (0,1), we use a Beta prior distribution which mimics the support between 0 and 1\. Formally, let

*π*(*p*) \=  
Beta(*a, b*)*,*	if *p* /\= *p*∗*.*

The priors chosen here are non-informative and conjugate to the posterior, hence the posterior loss distribution will be mainly data driven and have a closed form expression.

Lemma 2.1. *The BF for the UC backtest is given by,*

(*p*∗)*m*1 (1 — *p*∗)*m*0  
*BF*01 \= *β*(*a* \+ *m , b* \+ *m* ) *.*  
1	0

For a proof of Lemma 2.1 see Appendix A.1. Then using the derived BF01 from Eq. (2.1), the decision to reject the *H*0 will occur when,

(*p*∗)*m*1 (1 — *p*∗)*m*0  
BF01 \= *β*(*a* \+ *m , b* \+ *m* ) *\<* 1*,*	(2.12)  
1	0

where *β* corresponds to the *β*\-function. For the BLRT statistic, we can use Eq. (2.7) instead of the simulation method presented in Eq. (2.8). The following Theorem provides an analytical form for the BLRT statistic for the UC backtest, which is extremely useful in what follows.

Theorem 2.1. *The analytical form for the BLRT statistic for the UC backtest is given by,*

*TBLRT*(*y, p*) \= —2\[*Aπ*0 — *Bπ*1 \] \+ 1*,*	(2.13)

*where,*

*Aπ* \= *m*1 log(*p*∗) \+ *m*0 log(1 — *p*∗)*,*  
*Bπ*1 \= *m*1(*ψ*(*a* \+ *m*1) — *ψ*(*a* \+ *m*1 \+ *b* \+ *m*0)) — *m*0(*ψ*(*b* \+ *m*0) — *ψ*(*a* \+ *m*1 \+ *b* \+ *m*0))*,*

*and ψ corresponds to the digamma function.*

For a proof of Theorem 2.1 see Appendix A.2. Let *C*BLRT be determined using a required tail significance from a *χ*2(1)-distribution, then the decision to reject *H*0 will occur when *T*BLRT(*y, p*) *\> C*BLRT. A more formal representation for the test outcomes is shown in Table 1\.

Table 1: Criteria for the rejection or acceptance of the *H*0

Reject *H*0	Do not reject *H*0

*BF*01

(*p*∗)*m*1 (1−*p*∗)*m*0  
*β*(*a*\+*m*1*,b*\+*m*0)  *\<* 1

(*p*∗)*m*1 (1−*p*∗)*m*0  
*β*(*a*\+*m*1*,b*\+*m*0)  *\>* 1

*T*BLRT	*T*BLRT *\> CBLRT	T*BLRT *\< CBLRT*

3. Bayesian Model Estimation and Forecasting

Government interventions such as the introduction of Solvency II regulation has required insur- ance companies to strictly manage their reserves to reduce the risk of insolvency. Thus it becomes a crucial aspect for insurance services companies to not over or under compensate the required reserves which is contingent on the underlying mortality assumptions. This is particularly impor- tant to pension providers where management of pension payments are crucially dependent many risk factors including longevity risk (e.g., Konicz and Mulvey, 2015). In this Section, we develop

the Bayesian modelling estimation7 and forecasting procedures for applying the new backtesting technique developed in the previous section for the annuity liability experience in the insurance industry.

1. *Preliminaries*

One of the more renowned models in mortality modelling is the Lee and Carter (1992) model, which is commonly used as tool for mortality estimation and forecasting due to its simplistic model nature (Deb´on et al., 2008). Another widely accepted mortality model is the Cairns et al. (2009) model which offers accuracy of mortality rates for higher ages and non-age specific parameters. A possible downfall of the estimation procedure is that it requires two steps approach: firstly, a point estimation stage is produced, secondly a fitting stage is then conducted on the latent dynamics.

In this paper, we focus on a Bayesian estimation of both a linear variant of the LC and CBD mod- els, and a nonlinear variant based on Poisson and Binomial distributed death counts, respectively. A Kalman Filter alongside a Metropolis-Within-Gibbs sampler embedded in a MCMC algorithm will be used and this benefits two folds. Firstly, the Kalman Filter is a one-step procedure and is able to retain the state dynamics without the need for an extra fitting procedure, and secondly, we are able to retain the MCMC draws for posterior inference and parameter risk analysis.

Let *µx*(*t*) denote the force of mortality for an individual aged *x* at time *t*. Under the piecewise constant force of mortality assumption we have,

*µx*\+*s*(*t* \+ *s*) \= *mx,t*	for 0 ≤ *s \<* 1 and *x* ∈ N*,*

with *qx,t* \= 1 — *e*−*mx,t* , where *qx,t* represents the 1-year death probability for an individual aged *x*

at time *t*. Denote the crude central death rate and crude death rate as,

*m*˜ *x,t*

\= *dx,t , Ex,t*

*q*˜*x,t*

\= 1 — *e*−*m*˜*x,t,*	(3.1)

where *dx,t* is the number of deaths recorded at age *x* during year *t*, and *Ex,t* is the total population at age *x* during year *t*. The *N* \-year survival rate of a person aged *x* at time *t* can be calculated as

*Sx*(*t, N* ) \=

*n*Y\=1

(1 — *qx*\+*n,t*\+*n*) \= exp

—

*n*\=1

*mx*\+*n,t*\+*n*\!

*.*	(3.2)

7Arguments and some necessary details about the Bayesian state-space model estimation procedure can be found in SI Section 1.1.  
Further, we work in a discrete-time modelling environment. Let us assume *x* ∈ {*x*1*, . . . , xn*} and *t* ∈ {*t*1*, . . . , tT* }, where *x*1 represents the initial age of the dataset, *xn* represents the ultimate age of our dataset, *t*1 represents the initial year, *tT* corresponds to the final year used, for simplicity

we will represent *t*1 \= 1*, ..., tT* \= *T* , where *T* is the time horizon.

In the next section we will introduce the idea of MCMC and Bayesian model estimation, for more information regarding a general Bayesian modelling framework see SI Section 1.1.

2. *The Lee-Carter model*

Let *yx,t* := ln(*mx,t*)8, then the LC model assumes that the central mortality rate is governed by the following process,  
*yt* \= *α* \+ *βκt* \+ *εt,*	(3.3)

where *yt* := {*yx,t* : *x* ∈ (*x*1*, ..., xn*)}; *α*′ := {*αx* : *x* ∈ (*x*1*, ..., xn*)} and *β*′ := {*βx* : *x* ∈ (*x*1*, ..., xn*)} are age dependent variables, *κt* captures the time dynamics of the population common through all ages, and *εt* ∼ *N* (0*,* I*nσ*2). Here, I*n* represents the *n* × *n* identity matrix and a random walk with drift process will be used to model the latent state dynamics to facilitate the state-space formulation,

*κt* \= *κt*−1 \+ *δ* \+ *ωt,*	(3.4)

where *ωt* ∼ *N* (0*, σ*2 ) and *δ* represents the drift term of the process, furthermore *ωt* and *εt* are assumed to be independent. It is shown in Lee and Carter (1992) that the parametrization in Eq. (3.3) is not unique, which means that for a particular likelihood maximization there is an indefinite number of solutions to the maximum likelihood estimate. To rectify this situation Lee  
and Carter (1992) imposed the constraints, Σ*xn	βx* \= 1, and Σ*T	κt* \= 0\. In our case we will

also follow these constraints. For more information regarding the LC model, we refer to SI Section 1.2.

1. *Linear variant*

The LC model in linear state-space form is given by

*yt* \=*α* \+ *βκt* \+ *εt,	εt* ∼ *N* (0*,* I*nσ*2)	(3.5)

*κt* \=*κt*−1 \+ *δ* \+ *ωt,	ωt* ∼ *N* (0*, σ*2 )*,*	(3.6)

8As the central mortality rate cannot be observed, we can instead model the crude central mortality rate given by Eq. (3.1).

with the static model parameter vector ΘLC \= {*α, β, δ, σ*2 *, σ*2}. Recall that in the Bayesian setting,  
*ω	ε*

our aim is to draw samples from the joint posterior density *π*(*κ*1:*T ,* ΘLC|*y*1:*T* )*,* using Gibbs sampling, our MCMC procedure consists of

1. Initialise ΘLC \= Θ(0).

   2. For *i* \= 1*, . . . , M* ,

      1) sample *κ*(*i*)

         2) sample Θ(*i*)

from *π*(*κ*1:*T* |Θ(*i*−1\)*, y*1:*T* )*,*

from *π*(ΘLC|*κ*(*i*) *, y*1:*T* ).

A sample of the conditional distribution *π*(*κ*1:*tT* |ΘLC*, y*1:*tT* ) can be obtained via forward-backward

sampling using Kalman filtering (Carter and Kohn, 1994).  To draw samples from *π*(ΘLC|*κ*(*i*)

*, y*1:*tT* ),

we assume the following conjugate prior distributions:

*π*(*δ*) ∼ *N* (*µθ, σ*2)*,*

*π*(*σ*2) ∼ *I.G*(*aε, bε*)9,	*π*(*σ*2 ) ∼ *I.G*(*aω, bω*)  
*ε	ω*

*π*(*αx*) ∼ *N* (*µα, σ*2 ),	*π*(*βx*) ∼ *N* (*µβ, σ*2) for *x* ∈ {(*x*1*, ..., xn*)*.*  
*α	β*

The prior distributions were chosen such that when multiplied by the likelihood function, the resulting posterior distribution will be of the same family; this is known as the conjugacy property and it facilitates the Gibbs sampling procedure. In the case where no conjugacy is involved, the Metropolis-Hastings (MH) algorithm can be applied. The full conditional posterior distribution for ΘLC are as follows10:

2	2	2 Σ	*x*

2	2 −1	2

2	2  2 −1 

2	2	2 Σ	*x*	2 Σ	2	2  −1

2  2	2 Σ

2	2  −1 

*π*(*σ*2|*y, κ, β, α*) ∼ *I.G*(*aε* \+ *T n ,  bε* \+ 1 Σ Σ (*yx* — (*αx* \+ *βxκt*))2)  
*ε*	2

2	2	2 Σ  
2  
*t*\=1 *x*\=1  
*t*

2 2 −1	2 2

2	2 −1 

*π*(*σ*2 |*y, κ, δ*) ∼ *I.G*(*aω* \+ *T , bω* \+ (*κt* — (*κt*−1 \+ *δ*))2)  
*ω*	2

9The *I.G.* represents the Inverse Gamma distribution.  
10For a full derivation of posterior parameters and MCMC algorithm see Fung et al. (2017)

2. *Nonlinear variant*

For the Poisson model estimation under a Bayesian state-space framework, we use a Gibbs sampler, the EKF and a MH, embedded in an MCMC algorithm. Let first assume that the number of deaths *Dx,t* follows a Poisson distribution with rate *Ex,tmx,t*, where log(*mx,t*) is assumed to be the standard LC model. We have,

exp−E*x,tmx,t* (E*x,t*m*x,t*)d*x,t*  
*P* (*Dx,t* \= d*x,t*) \=  
*,*  
d*x,t*\!  
log(*E	m*	) \= h	*α* \+ log(*E*	)	*β*i  1  *,*

2  
*NLκt* \=*NLκt*−1 \+*NL δ* \+*NL ωt,	NLωt* ∼ *N* (0*,NL σ* )*.*

Let our static model parameter vector be defined as ΘPLC \= {*NLα, NLβ, NLδ, NLσ*2 *, NLσ*2}, then  
*ω	β*

our MCMC algorithm is as follows:

1. Initialise ΘPLC \= Θ(0) .

   2. For *i* \= 1*, . . . , M* ,

      1) Apply the EKF for *κ*(*i*) using the function EKF-LC *κt*(*NLα*(*i*)*, NLβ*(*i*)*, NLδ*(*i*)*, NL*(*σ*2 )(*i*)).

         2) Using the function MH-LC *κt*((*NL*

   draws from *π*(*κ*|Θ(*i*−1\)*, y*1:*T* ).

*κ*∗)(*i*)*,*

*NLκ*(*i*)*,*

*NLα*(*i*)*,*

*NLβ*(*i*)*,*

*NLδ*(*i*)*,*

*NL*(*σ*2 )(*i*)) produce

3) Using the function MH-LC *β*(*NLκ*(*i*)*, NLα*(*i*)*, NLβ*(*i*)*, NLδ*(*i*)*, NL*(*σ*2 )(*i*)*,* (*NLσ*2)(*i*)) produce

*ω	β*

draws from *π*(*κ*|Θ(*i*−1\)*, y*1:*T* ) for *κ*(*i*).

4) Gibbs sampling for Θ(*i*)	from *π*(ΘPLC|*κ*(*i*)*, y*1:*T* ).

A sample of the conditional distribution *π*(*κ*1:*tT* |ΘPLC*, y*1:*tT* ) is obtained via forward-backward sampling using the EKF and the MH algorithm. The full MCMC algorithm is shown in Appendix B.

To draw samples from *π*(Θ *π*(*NLδ*) ∼ *N* (*µδ, σ*2)*,*

PLC|*NL*

(*i*) 1:*tT*

*, y*1:*tT*

), we assume the following conjugate prior distributions:  
*π*(*NLσ*2 ) ∼ *I.G*(*aω, bω*),	*π*(*NLσ*2) ∼ *I.G*(*aβ, bβ*)  
*ω	β*

*π*(*NLαx*) ∼ LogGamma(*aα, bα*),	*π*(*NLβx*) ∼ *N* (*µβ, σ*2) for *x* ∈ {(*x*1*, ..., xn*)*.*

Non-informative priors were chosen to ensure the posterior distribution is mainly data driven. The conditional posterior distribution for ΘPLC are as follows11:

11For a derivation of the posterior distributions see Lemmas 1.1-1.5 (with their proofs) in SI Section 1.3

*π*(*NLαx*

|*y,*

*NLβ,*

*NLκ*) ∼ LogGamma(*aα*

*T*  
*t*\=1

d*x,t*

*, bα*

*T*  
*t*\=1

E*x,t*

exp(*NL*

*βx NL*

*κt*))*,*

*π*(  *σ*2|*y,*

*β*) ∼ I.G *a*  \+ *N , b*  \+ 1	*β	β*′ ,

2	2	2 Σ

2	2 −1	2	2	2

2 −1 

*π*(*NL*

*σ*2 |*y,*

*NLκ,*

*T*  
*NLδ*) ∼ *I.G*(*aω* \+	*, bω* \+ (*NLκt*

— (*NL*

*κt*−1

\+ *NL*

*δ*))2)*,*

the sampling procedure for *π*(*NLβx*|*y,NL κ,* ΘPLC) was accomplished via a Random Walk MH algo- rithm (see SI Algorithm 3).

3. *The Cairns-Blake-Dowd model*

The CBD model has a wide variety of applications ranging from actuarial pricing, longevity derivative pricing and mortality predictions. Cairns et al. (2006) proposed to model the dynamics of the true 1-year death rates as follows

*eκ*1*,t*\+*κ*2*,t*(*x*−*x*¯)  
*qx,t* \= 1 \+ *eκ*1*,t*\+*κ*2*,t*(*x*−*x*¯) *,*

or equivalently

ln	 *qx,t *	\= *κ*  
1 — *qx,t*

1*,t*

\+ *κ*2*,t*

(*x* — *x*¯)*,*	(3.7)

where *x*¯ \= *n*−1	*i xi* and the latent period factor *κt* := \[*κ*1*,t, κ*2*,t*\]′ is a multivariate random walk with drift process with non-trivial variance-covariance structure:

*κt* \= *θ* \+ *κt*−1 \+ *ωt,	ωt* ∼ *N* (0*,* Σ)*,*	(3.8)

where *θ* := \[*θ*1 *θ*2\]′ is the drift vector,and Σ is a 2 × 2 covariance matrix. For a more detailed analysis of the CBD model see SI Section 1.4

1. *Linear variant*

Since the true death probabilities, *qx,t*, are unobservable, we can instead model the observable crude death probabilities, *q*˜*x,t*, estimated using Eq. (3.1), which allows the CBD model to directly follow a linear structure shown in Eqs. (3.7) and (3.8). For convenience, let ΘCBD \= (*θ*1*, θ*2*, σ*2*,* Σ) denote the static parameter vector for the CBD model in Eq. (3.7) and with the introduction of an error component. Let *yx,t* := ln(*q*˜*x,t/*(1 — *q*˜*x,t*)), then the CBD model in linear state-space

representation is given by

*yx*1*,t* 	1	(*x*1 — *x*¯) *κ*		*νx*1*,t* 	*νx*1*,t*   
 .  \= .	.	  1*,t* \+  .  *,*  .  ∼ *N* (0*,* I *σ*2)*,*	(3.9)

*κ*1*,t* \= *θ*1 \+ *κ*1*,t*−1 \+ *ω*1*,t* *,*	*ω*1*,t* ∼ *N* (0*,* Σ)*,*	(3.10)  
*κ*2*,t*	*θ*2	*κ*2*,t*−1	*ω*2*,t*	*ω*2*,t*

where I*n* represents the *n* × *n* identity matrix. Eqs. (3.9) and (3.10) correspond to the measurement equation and the state equation respectively. A measurement error term, *νx,t*, was included in Eq. (3.9) to facilitate the linear Gaussian state-space model estimation. Since model (3.9) and (3.10) belongs to the class of linear and Gaussian state-space models, we can perform MCMC estimation of the model utilizing a multivariate Kalman filter. Similar to the case in the LC model, our aim is to draw samples from the joint posterior density *π*(*κ*1:*T ,* ΘCBD|*y*1:*T* ) using Gibbs sampling which is as follows:

1. Initialise ΘCBD \= Θ(0) .

   2. For *i* \= 1*, . . . , M* ,

      1) sample *κ*(*i*)

         2) sample Θ(*i*)

from *π*(*κ*1:*T* |Θ(*i*−1\)*, y*1:*T* ),

from *π*(ΘCBD|*κ*(*i*) *, y*1:*T* ).  
CBD	1:*T*

A sample from *π*(*κ*1:*T* |ΘCBD*, y*1:*T* ) can be obtained via a multivariate forward-backward sampling. To draw samples from the full conditional posterior distributions, we assume the following priors for ΘCBD,

*π*(*σ*2) ∼ *I.G*(*aν, bν*)*,	π*(*θi*) ∼ *N* (*µθ ,* Σ*θ* )*,	i* \= 1*,* 2*,*  
*ν	i*	*i*

*π*(Σ|(*σ*2*, σ*2)) ∼ *I.W*  (*ν* \+ 2\) — 1*,* 2*ξ* diag   1  *,*  1   *,*

2  *indep*	 1  1  

where I.W corresponds to the Inverse Wishart distribution, *Ak* are hyper-parameters, and the

*indep*  
notation	∼	corresponds to “independently distributed”. For more information for the MCMC

algorithm and posterior derivations, see Leung et al. (2018). Using the prior distributions described above, the posterior distributions for the static parameters are given by:  
*π*(*σ*2|*y, κ*) ∼ *I.G*(*aν* \+ *T n ,  bν* \+ 1 Σ Σ (*yx,t* — (*κ*1*,t* \+ (*x* — *x*¯)*κ*2*,t*))2),

*π*(*θ*|*y, κ,* Σ) ∼ *N*  (Σ−1 \+ *n*Σ−1)−1  Σ −1*µ* \+ *n*Σ−1 Σ*T*  \[*κ* — *κ*	\]  *,* Σ−1 \+ *T* Σ−1 −1 ,

*π*(*σ*2|Σ)

*i.i.d*  
\~ *I.G*(

*ξ*\+*T , ξ*\[Σ−1

\]*kk* \+   1   ) for *k* ∈ (1*,* 2),  
*k*

*π*(Σ|*σ*2*, σ*2*, y, κ, θ*) ∼ *I.W* (*ξ* \+ *T* \+ *n* — 1*,* 2*ξ* × *diag*(  1  *,*  1  ) \+ Σ*T*	\[*κ* − *θ*\] \[*κ* − *θ*\]′),

where \[Σ−1\]*kk* denotes the (*k, k*) element of \[Σ−1\]. Derivations of these posteriors are provided in SI Section 1.5. The choice of a hierarchical prior for Σ is to circumvent the issue of the Inverse-Wishart prior leading to a biased estimator for the correlation coefficient when the variances are small.12

2. *Nonlinear variant*

The Binomial model for the number of deaths is used for the CBD model due to its canonical link with the generalized dynamic linear model in mortality modelling. Instead of using the crude death rates, we use the observed number of deaths, and assume it follows a *B*(*n, p*), with *n* \= E*x,t*, *p* \= *qx,t*, and logit(*qx,t*) is defined as in Eq. (3.7). The nonlinear state-space framework is given as follows:

*P* (D

*x,t*

\= d*x,t*

) \=  E*x,t*  q  
d*x,t*

*x,t*

d*x,t* (1 — q

*x,t*

)E*x,t*−d*x,t,*  
logit(q	) \= h1 (*x* — *x*¯)i *NLκ*1*,t* *,*

*NLκ*1*,t* \= *NLθ*1 \+ *NLκ*1*,t*−1 \+ *ω*1*,t* *,*	*ω*1*,t* ∼ *N* (0*,*	Σ)*.*  
*NLκ*2*,t*	*NLθ*2	*NLκ*2*,t*−1	*ω*2*,t*	*ω*2*,t	NL*

With the static model parameter vector ΘBCBD \= {*NLθ*1*, NLθ*2*, NL*Σ}, the MCMC algorithm is as follows:

1. Initialise ΘBCBD \= Θ(0)	.

   2. For *i* \= 1*, . . . , M* ,

      1) Apply the EKF for *NL*

(*i*) 1:*T*

using the function EKF *κt*(*NL*

*θ*(*i*−1\)*,*

*NL*Σ(*i*))*.*

2) Using the function MH *κt*(*κ*∗ *, κ*∗ *,	κ ,*

*κ ,	θ,*

Σ) produce draws from

*π*(*NL*

*κ*1:*T*

(*i*−1\) BCBD

1:*T* ).

1·	2·  
*NL*  1·  
*NL*  2· *NL	NL*

3) Gibbs sampling for Θ(*i*)	from *π*(ΘBCBD|*κ*(*i*) *, y*1:*T* )*,*

12For more details the reader is referred to Section 2 of Leung et al. (2018).

where, *NL*

∗  
1·	*NL*

∗  
1*,*1:*T*

and *NL*

∗  
2·	*NL*

∗  
2*,*1:*T*

.	A sample from *π*(*NL*

*κ*1:*T*

|ΘCBD

*, y*1:*T*

) can be

obtained via an EKF with MH algorithm.  To draw samples from the posterior distributions,

*π*(ΘBCBD|*κ*(*i*) *, y*1:*T* ), we assume the following priors for ΘBCBD,

*π*(*NLθi*) ∼ *N* (*µθi,* Σ*θi* )*,	i* \= 1*,* 2*,*

1	2

2  *indep*

2	2  
1	2

 1   1  

Using the prior distributions described above, the posterior distributions for the static parameters are given by:

*π*(  *θ*|*y, κ,*	Σ) ∼ *N*  (Σ−1 \+ *n*  Σ−1)−1  Σ −1*µ* \+ *n*  Σ−1 Σ*T*  \[  *κ* —	*κ*	\]  *,* Σ−1 \+ *T*	Σ−1 −1 ,

*π*(*σ*2|*NL*Σ)

*i.i.d*  
\~ *I.G*(

*ξ*\+*T , ξ*\[  Σ−1

\]*kk* \+   1   ) for *k* ∈ (1*,* 2),  
*k*

*π*(  Σ|*σ*2*, σ*2*, y,	κ,	θ*) ∼ *I.W* (*ξ*\+*T* \+*n*—1*,* 2*ξ*×*diag*(  1  *,*  1  )+Σ*T*	\[	*κ* −	*θ*\] \[	*κ* −	′

where \[*NL*Σ−1\]*kk* denotes the (*k, k*) element of \[*NL*Σ−1\]. Derivations of these posteriors are provided in SI Appendix 1.5. The choice of a hierarchical prior for Σ is to circumvent the issue of the inverse-wishart prior leading to a biased estimator for the correlation coefficient when the variances are small13. Details for the MCMC algorithm including EKF are provided in Appendix C.

4. Empirical Results

In this section, we compare the results obtained from estimating the LC and the CBD models under the linear and nonlinear variants. We used the Human Mortality Database for the following list of countries: Australia, United Kingdom, Italy, France, Spain, New Zealand, Sweden, Germany, and Russia aged 50 to 95 total population, across time periods 1950 — 2000\. For countries where the mortality data does not date back to 1950, the most earliest year was used instead. A total of 20*,* 000 MCMC iterations are conducted, and the first 5*,* 000 was used as the burn-in period. Hyper- parameters were chosen to be non-informative, such that our posterior distribution will be mainly data driven. The hyper-parameter specifications are shown in SI Table 1, and they were identical for all countries. The Geweke statistic is a tool used in Bayesian statistics to determine whether the last iterations of the MCMC draws from the full conditional posteriors are different from the

13For more details the reader is referred to Leung et al. (2018)

first half of the iterations, if there is no statistical evidence of a difference we say that the chain has reached a stationary state. The Geweke Statistic shown in SI Tables 2 to 19, indicated that most parameters reached a stationary state with a 95% confidence. Furthermore, the trace-plots shown in SI Figures ?? and 11 indicates no apparent signs of serial correlation, and once again confirming our hypothesis that the chain has reached convergence. For more details on the LC and CBD parameter implications see SI Section 1.6.1.

1. *K-step ahead forecasting*

In this section we provide the algorithm to produce a *K*\-step ahead forecast for both the linear and nonlinear variants of the LC and CBD models. Under the Bayesian method of forecasting, we utilize our posterior draws which retain information about our parameter uncertainty to produce our *K*\-step ahead forecasts. The method to produce the forecasts for the LC and CBD model varies in the dimension of the variance-covariance matrix and drift term. Let us start by denoting *k* as the *kth* step ahead forecast, this is consistent with the notion used in Algorithms 1 and 2\. Furthermore, let *m* denote the *mth* iteration from the MCMC, where *M* is the number of kept iterations after the burn-in period. For the parameter estimation results and convergence statistics see SI Section 1.7.  
Algorithm 1 Bayesian *K* step ahead forecasting for the LC model

1: for *k* \= 1*, ..., K* do

2:	for *i* \= 1*, ...M* do  
*i*  
*T* \+*k*  
*i*  
*T* \+(*k*−1\)

\+ *δi,* (*σ*2 )*i*)  
4:	log(m˜ *i*	) ∼ *N* (*αi* \+ *βi κi*	(*σ*2)*i*) (Linear)  
*x,T* \+*k	x	x  T* \+*k	ε*  
5:	m*i*  
\= exp(*αi* \+ *βi κi*  
) (Nonlinear)  
*x,T* \+*k*  
6:	end for

7: end for  
*x	x T* \+*i*

Algorithm 2 Bayesian *K* step ahead forecasting for the CBD model

1: for *k* \= 1*, ..., K* do

2:	for *i* \= 1*, ...M* do  
*i*  
*T* \+*k*  
*i*  
*T* \+(*k*−1\)  
\+ *θi,* (*σ*2)*i*)  
4:	logit(q˜*i*  
) ∼ *N* ((*x* — *x*¯)*κi*  
*,* (*σ*2)*i*) (Linear)

exp((*x*−*x*¯)*κi*	)  
5:	q*i*	\= 	*T* \+*k*   (Nonlinear)  
*T* \+*k*

6:	end for

7: end for  
1+exp((*x*−*x*¯)*κi*	)

For both Algorithms 1 and 2, the latent states are taken from the *Forward Filtering Backward Sampling* (FFBS) algorithm, where the model static parameters are taken from Gibbs sampling at

the *mth* iteration. SI Section 1.7 shows a 10-step ahead forecast of *κt* from the LC model and *κt* from the CBD model. The 10-year ahead mortality forecasts for ages 50-90 in increments of 10 years over the years 2000 till 2010 was also produced. For example, *m*(90*, t*) will correspond to the mortality rate for the age 90 of a specified country across the time horizon of 2000 till 2010\.

5. The backtesting of stressed longevity trends

In this section, we apply a stress test procedure on the longevity trend with the aim of capturing longevity risk. In essence the idea is to obtain a liability estimate by stressing the mortality forecasts at the 0.5% interval, this in turn will trigger an increased in the liability estimate conditioned on improvements in life expectancy. Assume now we have a $1 continuously paid temporary annuity to a person currently aged *x* for the next *N* years. Let the price of a zero coupon bond which matures in *T* years be denoted as *B*(0*, T* ), we then have the liability for a $1 annuity paid to a person aged *x* at time *t* for the next *N* years to be,14

*N*

*Lx*(*N* ) \=	*B*(0*, n*)*Sx*(*t, n*)*.*	(5.1)

*n*\=1

We intentionally choose to not use market based annuity rates since besides longevity risk the premium will include company dependent factors such as profits and expenses. Eq. (5.1) will only be affected by longevity improvements over time and as such allows us to focus on longevity trend risk. First, let *N* be determined by our limiting age set at *ω* \= 95, for example if *x* \= 55 then *N* \= *ω* — *x*. Using our forecast intervals obtained in section 4.1, a mean and upper bound on *Lx*(*N* ) was obtained. Denote the mean of *Lx*(*N* ) as *L*mean(*N* ) \= *E*\[*Lx*(*N* )\] and the upper bound as *L*upper(*N* ), where *L*upper(*N* ) is calculated using the 0.5% quantile of the mortality forecasts15  
*x*	*x*

applied to Eq. (3.2), and thus would represent the liability estimated at the upper 99.5% quantile. In order to generate our out-of-sample forecasts, we used ages *x*1 \= 50 till *xn* \= *ω* \= 95, where the period of interest is from year 2001 till 2010\. The forecasts was obtained using the methods described in section 4.1 applied to *J* \= 9 different countries. Lastly, we obtain the following set:  
{(*L*mean(*N* )*, L*upper(*N* )) : *x* ∈ (50*, ...,* 95\)}.  
*x*	*x*

The capital requirement is a ratio which determines the extra capital amount needed to be held at time *t* for someone aged *x*, given that mortality is stressed at the 0.5% level. It is determined

14Here, *B*(0*, t*) := (  1  )*t*

15A lower quantile estimate of mortality forecast represents an increase of the annuity liability.  
![][image1]	![][image2]

1) Average over countries of the Percentage of extra capital required across ages 50 — 95\.

2) Average difference of Realised annuity and the upper 99% predicted annuity liabil- ity across ages 50 — 95 under both Lee-Carter model variants

Figure 1: LC model

using,

CapR \=

upper  
*L*mean(*N* ) — 1

× 100%*.*	(5.2)

Figures 1 and 2 represent the percentage of extra capital required for a 99% mortality stressed scenario. It is interesting to note that the linear and nonlinear variant of the LC model produced similar capital requirements and average difference across all countries for the realised annuity and 99.5% upper bound. Whereas on the contrary, the nonlinear CBD model produced largely varying results. The graph for the extra capital amount shows that the linear CBD model required a larger amount for all ages when compared with its nonlinear counterpart. Furthermore, we see that the average difference across all ages shows that it peaks for the higher age groups, this indicates that the linear CBD model overestimates the upper 99.5% annuity price. The findings can be summarized as follows. Firstly, the linear and nonlinear LC models show similar structures in the extra capital required and average difference of the upper annuity liability compared with the realised one, thus not much difference can be seen between the two models. The linear CBD model seems to over estimate the annuity liabilities and hence has the highest peak for the average difference curve, this is also reflected in the larger extra capital required to ensure a 99.5% of the annuity obligation can be met.

The idea of backtesting in the context of annuity pricing is to determine whether the stressed  
![][image3]	![][image4]

1) Average over countries of the Percentage of extra capital required across ages 50 — 95\.

   2) Average difference of Realised annuity and the upper 99% predicted annuity liability across ages 50 — 95 under both CBD model variants

Figure 2: CBD model

longevity scenarios were enough to capture the experienced liability over the forecasted time horizon from 2001 till 2013\. Our aim is to test whether the “hits” (when I \= 1\) follows a Be(*p*∗) distribution, where *p*∗ represents the quantile of interest, in our case we are interested in a longevity stressed scenario at the upper 99.5%, thus the probability of violations should be *p*∗ \= 0*.*005\. A backtesting procedure using BF and BLRT test statistic shown in Eqs. (2.12) and (2.13) will be used to determine the strength of evidence for the null and alternative models. This procedure statistically examines whether the frequency of exceptions for *N* \-year annuity liabilities is in line with the regulations of Solvency II. That is, whether companies are able to hold reserves capable of sustaining the liabilities in the long term. In this section we define “long term” to be capped at *ω* years, however this assumption can be relaxed. Let *j* represent a country used in Section 4 and denote *jL*∗(*N* ) for *x* ∈ (50*, ...,* 95\) as the sample path of our realised liabilities. Let us create an indicator variable, I*j*

where for a given interval forecast ( *L*mean(*N* )*,  L*upper(*N* )), we have  
*j  x	j  x*

1*,*	if  *L*∗(*N* ) ∈ ( *L*mean(*N* )*,	L*upper(*N* ))*,*

0*,*	if  *L*∗(*N* ) ∈*/* ( *L*upper(*N* )*,	L*upper(*N* ))*.*

We wish to test for I (*x*) ∼ *Be*(*p*∗). Let I ∗ := {I*j*(*t*) : *j* ∈ (1*, ..., J*)*, x* ∈ (50*, ...,* 95\)}, and let *m*  
*p	p	p*	1

and *m*0 denote the number of one and zero occurrences in I*p*∗ respectively. Then I*p*∗ will be a

vector of size *T* \= *m*1 \+ *m*0, and the joint likelihood function will be given by,

*l*(I*p*|*p*) \= *pm*1 (1 — *p*)*m*0 *.*	(5.4)

We assign the point mass prior under *H*0 : *p* \= *p*∗ and under the alternative *H*1 := *p* /\= *p*∗ we use a Beta(1,1) prior distribution which is a uniform over (0*,* 1). Let

with,

*π*(*p*) \=

Beta(1*,* 1\)*,*	if *p* /\= *p*∗*.*

(*p*∗)*m*1 (1 — *p*∗)*m*0  
BF01 \= *β*(*a* \+ *m , b* \+ *m* ) *.*  
1	0

For the BLRT statistic we find *T*BLRT(*y, θ*) \= —2\[*Aπ*0 — *Bπ*1 \] \+ 1 as defined in Eq. (2.13), with *p*∗ \= 0*.*005, *a* \= 0*.*5, and *b* \= 0*.*5\. Appendix Table 3 shows the violations across age groups and countries, and also results of the extra capital required and difference from realised annuity liability.16  
Table 2 contains the BF and BLRT statistic for each variant of the LC and CBD model by tallying the “ones” from Appendix Table 3\. A higher value for BF01 represents evidence favouring *H*0, meaning that indeed the violations occur at frequency of *p*∗. For values smaller than 1, it shows evidence towards *H*1, that violations do not follow a frequency of *p*∗. For the BLRT statistic, we compare it against the *χ*2\-distribution with 1 degrees of freedom. At the 5% region, the critical value (*C*BLRT) is 2*.*841\. A variety of prior specifications was conducted as a means of robustness check, however the goal of choosing a diffuse prior still applies. Besides the Beta(0.5,0.5) distribution corresponding to Jeffreys Prior, the Beta(*ǫ*¯,*ǫ*¯) known as Haldane’s prior and the Neutral-Information (NI) Beta( 1 , 1 ) prior was also used.17  
3 3

Furthermore, we can back-solve BF01 to obtain an implicit *p*ˆ, which represents the true frequency rate implied by the model. *p*ˆ can be found by,

(*p*)*m*1 (1 — *p*)*m*0  
*p*ˆ \= min	*.*	(5.5)  
*p*∈(0*,*1\) *β*(*a* \+ *m*1*, b* \+ *m*0)

16For the full table of results see SI Section 2\.  
17Here, *ǫ*¯ represents a small positive real number (*ǫ*¯ ∈ R\+).

Table 2: Derived BF and BLRT under the linear and nonlinear LC and CBD models across varying prior hyper-parameter specifications.

LC model

Linear	Nonlinear

Hyper-Parameters  Haldanes-Beta(*ǫ*¯,*ǫ*¯)	NI-Beta( 1 , 1 )	Jeffreys-Beta(0.5,0.5) Haldanes-Beta(*ǫ*¯,*ǫ*¯)  NI-Beta( 1 , 1 )  Jeffreys-Beta(0.5,0.5)  
 	   
3  3	3  3

Bayes Factor	8*.*472522 × 10−09	2*.*556865 × 10−08	4*.*431379 × 10−08	2*.*8695 × 10−06	9*.*2722 × 10−09	1*.*6618 × 10−05  
BLRT	37.0473	37.0613	37.0635	25.1922	25.2094	25.2120

*p*ˆ	0.039	0.039	0.039	0.031	0.031	0.031

CBD model

Linear	Nonlinear

Hyper-Parameters  Haldanes-Beta(*ǫ*¯,*ǫ*¯)	NI-Beta( 1 , 1 )	Jeffreys-Beta(0.5,0.5) Haldanes-Beta(*ǫ*¯,*ǫ*¯)  NI-Beta( 1 , 1 )  Jeffreys-Beta(0.5,0.5)  
 	   
3  3	3  3

Bayes Factor	0.0000	0.3492	1.4415	0.5394	3.3818	8.2784

BLRT	5.1504	4.4837	4.1510	\-0.0790	0.0350	0.0430

*p*ˆ	NA	NA	NA	0.005	0.005	0.005

As we observe in Table 2, the outcomes of both test statistics and *p*ˆ is shown. Both the LC models presented with a rejection of *H*0 under the BF and BLRT, meaning that a frequency of *p*∗ was rejected. In particular since the BF can be compared between models, we see that the nonlinear version of the LC model presents as a stronger model compared with its linear variant due to its larger BF, with its resulting *p*ˆ closer to *p*∗. The nonlinear CBD model performed the best out of the group, this can be seen from the BF and BLRT statistic giving evidence for *H*0 and the BF being the largest of the models. Its implicit *p*ˆ of 0.005 in Table 2 also shows that the model achieved the correct mortality coverage. It is interesting to note that although the linear CBD model was not able to achieve the correct coverage, it was due to it having no violations across all countries and ages. This meant that the linear CBD model overestimated the mortality rate and was able to capture the realised longevity liability in all cases. From a pricing perspective, although the linear variant of the CBD model captured all realised liabilities under its mortality forecasts, the liability estimates over the long run would over compensate for more than 0.5% under the longevity stress trend scenario. In a scenario where we are trying to minimize the capital required in order to achieve a 0*.*5% coverage, the nonlinear CBD model out-performed all models. With varying prior specifications, the test outcomes said mostly consistent. Under Jeffreys prior, the linear CBD model also seemed to not reject the *H*0 hypothesis, however if we compare that to the nonlinear CBD model, it is over 8 times more likely to not reject the *H*0. As pointed out by Li et al. (2014), the BLRT seems to have the least deviations with prior changes, mainly due to its loss function being averaged over the posterior rather than the prior distribution as in the BF.

6. Conclusion

In this paper we develop a new approach to backtesting under the Bayesian paradigm which can be an excellent tool for decision and policy makers and its demonstrated effectiveness establishes its excellent potential for a much broader area of applications. We utilized tools from Bayesian decision theory to determine test outcomes from the UC test and as an application we used annuity liabilities in a longevity stressed scenario from two renowned mortality models, the LC model and CBD model. To keep the framework aligned in the Bayesian paradigm, we chose to undergo a Bayesian model estimation in the linear and nonlinear state-space framework. Using the dynamic linear model structure, we modelled the central death counts using the Poisson distribution under the LC model and Binomially distributed death rates using the CBD model. We show that their nonlinear variants benefited more so when backtested under the UC test.

As a natural extension of our work, one could consider the multivariate version of our newly proposed backtest which would have to account for possible correlations in VaR-violations across different types of annuities and time. Moreover, we want to develop a set of tests of i.i.d. VaR- violations, and of course, of conditional coverage under the same Bayesian decision theoretic frame- work. As these issues are beyond the scope of the present paper, we will address them in our future research.

Acknowledgement The authors would like to thank the participants at the Quantitative Fi- nance and Risk Analysis (QFRA) 2019 and seminars at Boston University, University of Liverpool, Monash University and Shanghai University for helpful comments. Any remaining errors are ours.

References

Berger, J. O. and Sellke, T. (1987). Testing a point null hypothesis: The irreconcilability of *p* values and evidence. *Journal of the American Statistical Association*, 82(397):112–122.

Berkowitz, J. and O’Brien, J. (2002). How accurate are value-at-risk models at commercial banks?

*The Journal of Finance*, 57(3):1093–1111.

Cairns, A., Blake, D., and Dowd, K. (2006). A two-factor model for stochastic mortality with parameter uncertainty: Theory and calibration. *Journal of Risk and Insurance*, 73(4):687–718.

Cairns, A. J., Blake, D., Dowd, K., Coughlan, G. D., Epstein, D., Ong, A., and Balevich, I. (2009).

A quantitative comparison of stochastic mortality models using data from england and wales and the united states. *North American Actuarial Journal*, 13(1):1–35.

Campbell, S. D. (2007). A review of backtesting and backtesting procedures. *Journal of Risk*, 9(2):1–18.

Carter, C. K. and Kohn, R. (1994). On Gibbs sampling for state space models. *Biometrika*, 81(3):541–553.

Christoffersen, P. (2009). Value–at–risk models. In *Handbook of Financial Time Series*, pages 753–766. Springer.

Christoffersen, P. and Pelletier, D. (2004). Backtesting value-at-risk: A duration-based approach.

*Journal of Financial Econometrics*, 2(1):84–108.

Christoffersen, P. F. (1998). Evaluating interval forecasts. *International Economic Review*, 4(39):841–862.

Deb´on, A., Montes, F., and Puig, F. (2008). Modelling and forecasting mortality in Spain. *European Journal of Operational Research*, 189(3):624 – 637\.

Drenovak, M., Rankovi´c, V., Ivanovi´c, M., Uroˇsevi´c, B., and Jelic, R. (2017). Market risk man- agement in a post-Basel II regulatory environment. *European Journal of Operational Research*, 257(3):1030–1044.

Eckert, J. and Gatzert, N. (2018). Risk-and value-based management for non-life insurers under solvency constraints. *European Journal of Operational Research*, 266(2):761–774.

Fung, M. C., Peters, G. W., and Shevchenko, P. V. (2017). A unified approach to mortality mod- elling using state-space framework: characterisation, identification, estimation and forecasting. *Annals of Actuarial Science*, 11(2):343–389.

Glasserman, P., Heidelberger, P., and Shahabuddin, P. (2002). Portfolio value-at-risk with heavy- tailed risk factors. *Mathematical Finance*, 12(3):239–269.

Goodman, S. N. (2001). Of *p*\-values and bayes: a modest proposal. *Epidemiology*, 12(3):295–297.

Hari, N., De Waegenaere, A., Melenberg, B., and Nijman, T. E. (2008). Longevity risk in portfolios of pension annuities. *Insurance: Mathematics and Economics*, 42(2):505–519.

Harvey, C. R. (2017). Presidential address: the scientific outlook in financial economics. *The Journal of Finance*, 72(4):1399–1440.

Konicz, A. K. and Mulvey, J. M. (2015). Optimal savings management for individuals with defined contribution pension plans. *European Journal of Operational Research*, 243(1):233–247.

Kupiec, P. H. (1995). Techniques for verifying the accuracy of risk measurement models. *The Journal of Derivatives*, 3(2):73–84.

Lee, R. D. and Carter, L. R. (1992). Modeling and forecasting us mortality. *Journal of the American Statistical Association*, 87(419):659–671.

Leung, M., Fung, M. C., and O‘Hare, C. (2018). A comparative study of pricing approaches for longevity instruments. *Insurance: Mathematics and Economics*, 82:95 – 116\.

Li, Y., Zeng, T., and Yu, J. (2014). A new approach to bayesian hypothesis testing. *Journal of Econometrics*, 178:602–612.

Nieto, M. R. and Ruiz, E. (2016). Frontiers in VaR forecasting and backtesting. *International Journal of Forecasting*, 32(2):475–501.

Plat, R. (2011). One-year value-at-risk for longevity and mortality. *Insurance: Mathematics and Economics*, 49(3):462–470.

Wied, D., Weiß, G. N., and Ziggel, D. (2016). Evaluating value-at-risk forecasts: A new set of multivariate backtests. *Journal of Banking & Finance*, 72:121–132.

Ziggel, D., Berens, T., Weiß, G. N., and Wied, D. (2014). A new set of improved value-at-risk backtests. *Journal of Banking & Finance*, 48:29–41.

Appendix A	Bayesian Testing

1. *Proof of Lemma 2.1*

When testing two hypotheses, *H*0 and *H*1, where *H*0 is a point null hypothesis and *H*1 is a composite hypothesis, the BF is given by,

*l*(*y*|*θ* \= *θ*0)	*. π*(*y*|*θ, H* )*π*(*θ*|*H* )*dθ*

Under the UC backtest assumptions, the sequence of ones and zeros are assumed to follow a Bernoulli distribution, hence the likelihood function for the data corresponds to,

*m*  
*l*(I|*p*) \=	*pyi* (1 — *p*)1−*yi* \= *pm*1 (1 — *p*)*m*0 *,*

*i*\=1

where *m* is the number of data points, *m*1 represents the number of “ones” in the data, likewise *m*0 corresponds to the number of “zeros”. The null hypothesis is defined as *p* \= *p*∗ for a given *p*∗, and the alternative hypothesis as *p* /\= *p*∗. With the following prior specifications for *p*:

*π*(*p*) \=  
Beta(*a, b*)*,*	if *p* /\= *p*∗*.*

We derive an analytical form for the BF due to the conjugate property of the Beta-Binomial distribution, i.e.,

*l*(*y*|*p* \= *p*∗)  
∫	*l*(*y*|*θ*)*π*(*θ*)*dθ* \= ∫

*p*/\=*p*∗

(*p*∗)*m*1 (1 — *p*∗)*m*0  
*pm*1 (1 — *p*)*m*0 Beta(*a, b*)*dp*

(*p*∗)*m*1 (1 — *p*∗)*m*0  
\=  
*β*(*m*1

\+ *a, m*0  
\+ *b*) ∫

*p*/\=*p*∗

*pm*1+*a*−1(1−*p*)*m*0+*b*−1

*β*(*m*1\+*a,m*0\+*b*)  
(*p*∗)*m*1 (1 — *p*∗)*m*0  
\=	*.*  
*β*(*m*1 \+ *a, m*0 \+ *b*)

2. *Proof of Theorem 2.1*

To derive the analytical form for the BLRT for the UC test, we begin with the test statistic,

*T*BLRT(*y, θ*) \= — 2 ∫ log(*l*(*y*|*θ*0))*π*(*θ*|*y*)*dθ* — ∫ log(*l*(*y*|*θ*))*π*(*θ*|*y*)*dθ* \+ 1*.*  
\`*θ*	˛¸	x	\`	˛¸	

Here, it can be shown that integral (1) can be decomposed to the following:

log(*l*(*y*|*θ*0))*π*(*θ*|*y*)*dθ* \=  
*θ	θ*

log((*θ*

∗)*m*

1 (1 — *θ*

∗)*m*0 )

*θa*\+*m*1−1(1 — *θ*)*b*\+*m*0−1  
*dθ*  
*β*(*a* \+ *m*1*, b* \+ *m*0)

\=*m*1 log(*θ*∗) \+ *m*0 log(1 — *θ*∗)*.*

(A.1)

Now, expanding integral (2), we have:

∫ log(*l*(*y*|*θ*))*π*(*θ*|*y*)*dθ* \= ∫

\[*m*1 log(*θ*) \+ *m*0 log(1 — *θ*)\]

*θa*\+*m*1−1(1 — *θ*)*b*\+*m*0−1  
*dθ.*  
*β*(*a* \+ *m , b* \+ *m* )  
*θ*

*m*1 log(*θ*)  
*θ*  
*θ*

*θa*\+*m*1−1(1 — *θ*)*b*\+*m*0−1

*β*(*a* \+ *m*1*, b* \+ *m*0)

*dθ* \=

	*m*1	

*β*(*a* \+ *m*1*, b* \+ *m*0)

log(*θ*)*θ*  
*θ*  
1

*a*\+*m*1−1  
0

(1 — *θ*)

*b*\+*m*0−1*dθ*

	*m*1	  
\=  
*β*(*a* \+ *m*1*, b* \+ *m*0)

*∂θa*\+*m*1−1

*θ	∂a*

(1 — *θ*)

*b*\+*m*0−1*dθ*

	*m*1	*∂β*(*a* \+ *m*1*, b* \+ *m*0)  
\=  
*β*(*a* \+ *m*1*, b* \+ *m*0)	*∂a*

\= *m*1*∂* log(*β*(*a* \+ *m*1*, b* \+ *m*0))  
*∂a*

\= *m*1*∂* log(Γ(*a* \+ *m*1)) — *m*1*∂* log(Γ(*a* \+ *m*1 \+ *b* \+ *m*0))  
*∂a	∂a*

\=*m*1(*ψ*(*a* \+ *m*1) — *ψ*(*a* \+ *m*1 \+ *b* \+ *m*0))*.*

∫ *m*0 log(1 — *θ*)

*θa*\+*m*1−1(1 — *θ*)*b*\+*m*0−1  
*dθ* \=  
*β*(*a* \+ *m , b* \+ *m* )

*m*0 log(1 — *θ*)

*θa*\+*m*1−1(1 — *θ*)*b*\+*m*0−1  
*dθ*  
*β*(*a* \+ *m , b* \+ *m* )

(A.2)  
*θ*	1	0	*θ*	1	0

\= 	*m*0	  
*β*(*a* \+ *m*1*, b* \+ *m*0)

log(*θ*)*θa*\+*m*1 (1 — *θ*)*b*\+*m*0 *dθ*  
*θ*

	*m*0	  
\=  
*β*(*a* \+ *m*1*, b* \+ *m*0)

*∂θa*\+*m*1−1

*θ	∂a*

(1 — *θ*)

*b*\+*m*0−1*dθ*

	*m*0	*∂β*(*a* \+ *m*1*, b* \+ *m*0)  
\=  
*β*(*a* \+ *m*1*, b* \+ *m*0)	*∂a*

\= *m*0*∂* log(*β*(*a* \+ *m*1*, b* \+ *m*0))  
*∂a*

\= *m*0*∂* log(Γ(*a* \+ *m*1)) — *m*1*∂* log(Γ(*a* \+ *m*1 \+ *b* \+ *m*0))  
*∂a	∂a*

\=*m*0(*ψ*(*b* \+ *m*0) — *ψ*(*a* \+ *m*1 \+ *b* \+ *m*0))*.*

(A.3)

Combing Eqs. (A.1), (A.2), and (A.3), we retrieve the analytical form for th BLRT statistic.

*T*BLRT(*y, θ*) \= —2\[*m*1 log(*θ*∗) \+ *m*0 log(1 — *θ*∗) — (*m*1(*ψ*(*a* \+ *m*1) — *ψ*(*a* \+ *m*1 \+ *b* \+ *m*0))+

*m*0(*ψ*(*b* \+ *m*0) — *ψ*(*a* \+ *m*1 \+ *b* \+ *m*0)))\] \+ 1*,*  (A.4)

as required.

Appendix B	MCMC Algorithm for the Lee-Carter Poisson model

1) Set initial values for the parameter vector (*α*0*, β*0*, κ*0*, δ*0*,* (*σ*2 )0*,* (*σ*2)0).

   *ω	β*

   2) Conditional on (*α*(*i*−1\)*, β*(*i*−1\)*, δ*(*i*−1\)), apply the EKF and Backward Smoother shown in Algorithm 1 of SI to obtain *κ*∗ as the candidate for step (iii).

      3) Simulate *κ*(*i*) using the MH step for *κt* shown in Algorithm 2 of SI, the candidate draw is taken from step (*ii*) to obtain the density *f* ∗ and *κ*(*i*−1\) is used to compute the density *f* .

      4) Simulate *β*(*i*) using the MH step for *βx* shown in Algorithm 3 of SI.

      5) Draw *α*(*i*) from the transformed posterior LogGamma(*a* \+Σ d	*, b* \+Σ E	exp(*β*(*i*−1\)*κ*(*i*−1\))).

      6) Draw *δ*(*i*) from its posterior distribution *N* (*µ, σ*2), with *µ* \= 1*/*(  1  \+   *T* −1   )(1*/*((*σ*2 )(*i*−1\))) Σ (*κ*(*i*)—

*t*−1

100

(*σ*2 )(*i*−1\)	*ω*

7) Draw (*σ*2)(*i*) from its posterior distribution *I.G*(*aβ* \+ *n/*2*, bβ* \+ (1*/*2\)*ββ*′)*.*

   8) Draw (*σ*2 )(*i*) from *I.G*(*aω* \+ (*T* — 1\)*/*2*, bω* \+ (1*/*2\) Σ ((*κ*(*i*) — *κ*(*i*) ) — *δ*(*i*))2)*.*

      9) Conditional on *κ*(*i*)*, α*(*i*)*, β*(*i*−1\)*,* (*σ*2 )(*i*)*,* (*σ*2)(*i*), simulate *β*(*i*) using Algorithm 3 with tuning

*ω	β*

parameter *σ*2.

Appendix C	MCMC Algorithm for the CBD Binomial model

1) Set initial values for the parameter vector (*κ*0 *, κ*0 *, θ*0*,* Σ0).

   1	2

2) Conditional on (*θ*(*i*−1\)*,* Σ(*i*−1\)), apply the EKF and Backward Smoother shown in Algorithm 4 of SI to obtain *κ*∗ as the candidate for step (iii).

3) Simulate *κ*(*i*) using the MH step for *κ* shown in Algorithm 5 of SI. The candidate draw, *κ*∗, is taken from step (*ii*) to obtain the density *f* ∗ and *κ*(*i*−1\) is used to compute the density *f* .

5) Draw *θ*(*i*) from its posterior distribution *π*(*θ*(*i*)|*y, κ*(*i*)*, κ*(*i*)*,* Σ(*i*−1\)).

   1	2

6) Draw Σ(*i*) from its posterior distribution *π*(Σ(*i*)|*y, κ*(*i*)*, κ*(*i*)*, θ*(*i*)) for *k* ∈ 1*,* 2\.

   *kk	kk*	1	2

7) Draw Σ(*i*) from its posterior distribution *π*(Σ(*i*)|Σ(*i*)*, y, κ*(*i*)*, κ*(*i*)*, θ*(*i*)).

   *ω	kk*	1	2

Appendix D	Annuity Liability Results

Table 3: Table showing the percentage of extra capital required, difference from realised annuity, and the indicator variable *j*I*x*(*N* ) over  
all countries used under the linear and nonlinear LC and CBD models.

LC model: Linear variant

Australia	United Kingdom	Italy	France	Spain	New Zealand	Sweden	Germany	Russia

	

|  | *x* |  | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) |  | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) |  | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) *p* |
| :---- | ----- | :---- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | :---- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | :---- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | 62 |  | 1.0871 | 0.0345 | 0 | 1.3976 | \-0.0027 | 1 | 1.4167 | 0.0346 | 0 |  | 1.3211 | 0.0754 | 0 | 1.6937 | 0.1345 | 0 | 1.2647 | 0.0457 | 0 |  | 0.7653 | 0.0139 | 0 | 1.1181 | 0.0007 | 0 | 2.9916 | 0.1953 | 0 |
|  | 63 |  | 1.1863 | 0.0400 | 0 | 1.5136 | \-0.0126 | 1 | 1.5539 | 0.0459 | 0 |  | 1.4437 | 0.0793 | 0 | 1.8621 | 0.1560 | 0 | 1.3784 | 0.0342 | 0 |  | 0.8516 | 0.0229 | 0 | 1.2135 | \-0.0093 | 1 | 2.9308 | 0.0746 | 0 |
|  | 64 |  | 1.2891 | 0.0432 | 0 | 1.6438 | \-0.0277 | 1 | 1.7054 | 0.0484 | 0 |  | 1.5849 | 0.0882 | 0 | 2.0546 | 0.1594 | 0 | 1.4972 | 0.0355 | 0 |  | 0.9434 | 0.0225 | 0 | 1.3135 | 0.0030 | 0 | 2.8399 | 0.1390 | 0 |
|  | 65 |  | 1.4045 | 0.0434 | 0 | 1.7866 | \-0.0260 | 1 | 1.8837 | 0.0725 | 0 |  | 1.7383 | 0.1028 | 0 | 2.2676 | 0.1615 | 0 | 1.6369 | 0.0540 | 0 |  | 1.0441 | 0.0450 | 0 | 1.4354 | 0.0105 | 0 | 2.7367 | 0.1525 | 0 |
|  | 66 |  | 1.5266 | 0.0409 | 0 | 1.9488 | \-0.0182 | 1 | 2.0850 | 0.0875 | 0 |  | 1.9075 | 0.1149 | 0 | 2.5059 | 0.1859 | 0 | 1.7883 | 0.0644 | 0 |  | 1.1604 | 0.0651 | 0 | 1.5661 | 0.0700 | 0 | 2.6445 | 0.1601 | 0 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | 67 |  | 1.6674 | 0.0451 | 0 | 2.1263 | \-0.0152 | 1 | 2.2985 | 0.1191 | 0 |  | 2.1026 | 0.1409 | 0 | 2.7705 | 0.1993 | 0 | 1.9546 | 0.0775 | 0 |  | 1.2778 | 0.0583 | 0 | 1.7244 | 0.0553 | 0 | 2.5420 | 0.0837 | 0 |
|  | 68 |  | 1.8089 | 0.0494 | 0 | 2.3145 | \-0.0063 | 1 | 2.5403 | 0.1292 | 0 |  | 2.3119 | 0.1550 | 0 | 3.0570 | 0.2183 | 0 | 2.1262 | 0.1207 | 0 |  | 1.4140 | 0.0878 | 0 | 1.8940 | 0.0893 | 0 | 2.5299 | 0.1208 | 0 |
|  | 78 |  | 3.6317 | 0.1937 | 0 | 4.8381 | 0.3167 | 0 | 6.0905 | 0.4478 | 0 |  | 5.3598 | 0.3220 | 0 | 6.3595 | 0.3362 | 0 | 4.3679 | 0.3027 | 0 |  | 3.3127 | 0.2586 | 0 | 4.6747 | 0.2946 | 0 | 4.5228 | \-0.0945 | 1 |
|  | 79 |  | 3.7922 | 0.2315 | 0 | 5.1090 | 0.3803 | 0 | 6.4520 | 0.4760 | 0 |  | 5.7091 | 0.3397 | 0 | 6.5175 | 0.3137 | 0 | 4.6064 | 0.4092 | 0 |  | 3.4933 | 0.3098 | 0 | 5.0275 | 0.3529 | 0 | 4.9417 | \-0.0125 | 1 |
|  | 83 |  | 4.4613 | 0.3334 | 0 | 5.9857 | 0.4174 | 0 | 7.6583 | 0.5039 | 0 |  | 6.7247 | 0.3379 | 0 | 6.6271 | 0.2436 | 0 | 5.6131 | 0.4988 | 0 |  | 4.1458 | 0.3883 | 0 | 6.1867 | 0.2771 | 0 | 7.3121 | \-0.0343 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | 89 |  | 3.3419 | 0.2215 | 0 | 4.3346 | 0.2995 | 0 | 5.5666 | 0.2744 | 0 |  | 4.8763 | 0.2055 | 0 | 3.4448 | \-0.0029 | 1 | 4.5050 | 0.3767 | 0 |  | 3.2734 | 0.2785 | 0 | 5.2542 | 0.1695 | 0 | 11.1593 | 0.1917 | 0 |
|  | 90 |  | 3.0166 | 0.1994 | 0 | 3.8785 | 0.2400 | 0 | 5.0126 | 0.2081 | 0 |  | 4.3462 | 0.1607 | 0 | 2.9596 | \-0.0044 | 1 | 4.1780 | 0.3092 | 0 |  | 2.9890 | 0.2129 | 0 | 4.9491 | 0.1366 | 0 | 11.0033 | 0.1582 | 0 |
|  | 91 |  | 2.7074 | 0.1729 | 0 | 3.4274 | 0.2243 | 0 | 4.3573 | 0.1942 | 0 |  | 3.7929 | 0.1780 | 0 | 2.3229 | \-0.0517 | 1 | 3.8098 | 0.2965 | 0 |  | 2.6991 | 0.2141 | 0 | 4.4998 | 0.1203 | 0 | 11.6785 | 0.1490 | 0 |
|  | 93 |  | 2.0600 | 0.1206 | 0 | 2.4038 | 0.1287 | 0 | 2.9633 | 0.1280 | 0 |  | 2.5141 | 0.1001 | 0 | 1.6598 | \-0.0240 | 1 | 2.8808 | 0.2030 | 0 |  | 2.0125 | 0.1506 | 0 | 3.4585 | 0.0721 | 0 | 8.3450 | 0.1345 | 0 |
|  | 94 |  | 1.6045 | 0.0888 | 0 | 1.8104 | 0.0776 | 0 | 2.2519 | 0.0757 | 0 |  | 1.8733 | 0.0527 | 0 | 1.3483 | \-0.0252 | 1 | 2.2760 | 0.1381 | 0 |  | 1.5699 | 0.0976 | 0 | 2.7775 | 0.0496 | 0 | 6.5192 | 0.0965 | 0 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

*p	p	p	p	p	p	p	p*

LC model: Nonlinear variant

Australia	United Kingdom	Italy	France	Spain	New Zealand	Sweden	Germany	Russia

	

|  | *x* |  | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) |  | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) |  | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) | CapR(%) | ∆*R* | *j* I*x*(*N* ) *p* |
| :---- | ----- | :---- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | :---- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | :---- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | 63 |  | 1.2695 | 0.0503 | 0 | 1.7360 | \-0.0052 | 1 | 1.6612 | 0.0471 | 0 |  | 1.5021 | 0.0803 | 0 | 2.0136 | 0.1692 | 0 | 1.4916 | 0.0420 | 0 |  | 1.0001 | 0.0261 | 0 | 0.8158 | \-0.0071 | 1 | 3.4137 | 0.0808 | 0 |
|  | 64 |  | 1.3791 | 0.0545 | 0 | 1.8832 | \-0.0182 | 1 | 1.8260 | 0.0508 | 0 |  | 1.6402 | 0.0890 | 0 | 2.2261 | 0.1744 | 0 | 1.6240 | 0.0450 | 0 |  | 1.1102 | 0.0267 | 0 | 0.8634 | 0.0025 | 0 | 3.2759 | 0.1433 | 0 |
|  | 65 |  | 1.4949 | 0.0559 | 0 | 2.0537 | \-0.0133 | 1 | 2.0143 | 0.0753 | 0 |  | 1.8048 | 0.1044 | 0 | 2.4505 | 0.1777 | 0 | 1.7636 | 0.0643 | 0 |  | 1.2315 | 0.0505 | 0 | 0.9456 | 0.0114 | 0 | 3.1094 | 0.1537 | 0 |
|  | 66 |  | 1.6245 | 0.0554 | 0 | 2.2286 | \-0.0037 | 1 | 2.2267 | 0.0908 | 0 |  | 1.9833 | 0.1172 | 0 | 2.7054 | 0.2038 | 0 | 1.8948 | 0.0736 | 0 |  | 1.3728 | 0.0714 | 0 | 1.0541 | 0.0751 | 0 | 2.9430 | 0.1604 | 0 |
|  | 91 |  | 2.3049 | 0.1302 | 0 | 3.2832 | 0.1903 | 0 | 4.3565 | 0.1690 | 0 |  | 3.6473 | 0.1583 | 0 | 1.9845 | \-0.0045 | 1 | 3.6316 | 0.2798 | 0 |  | 2.5641 | 0.1658 | 0 | 1.8977 | 0.0736 | 0 | 10.3803 | 0.1823 | 0 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | 93 |  | 1.7617 | 0.0904 | 0 | 2.2035 | 0.1038 | 0 | 2.8844 | 0.1119 | 0 |  | 2.4057 | 0.0867 | 0 | 1.3278 | \-0.0075 | 1 | 2.9968 | 0.2011 | 0 |  | 1.8977 | 0.1172 | 0 | 1.3124 | 0.0389 | 0 | 7.7978 | 0.1469 | 0 |
|  | 94 |  | 1.4047 | 0.0676 | 0 | 1.6078 | 0.0588 | 0 | 2.1721 | 0.0629 | 0 |  | 1.7553 | 0.0420 | 0 | 1.0020 | \-0.0190 | 1 | 2.4746 | 0.1397 | 0 |  | 1.5227 | 0.0749 | 0 | 1.0246 | 0.0259 | 0 | 6.0321 | 0.1054 | 0 |
|  | 63 |  | 1.2695 | 0.0503 | 0 | 1.7360 | \-0.0052 | 1 | 1.6612 | 0.0471 | 0 |  | 1.5021 | 0.0803 | 0 | 2.0136 | 0.1692 | 0 | 1.4916 | 0.0420 | 0 |  | 1.0001 | 0.0261 | 0 | 0.8158 | \-0.0071 | 1 | 3.4137 | 0.0808 | 0 |
|  | 76 |  | 3.3241 | 0.1787 | 0 | 4.8855 | 0.3000 | 0 | 5.6138 | 0.4152 | 0 |  | 4.8224 | 0.3075 | 0 | 6.3248 | 0.4009 | 0 | 3.9225 | 0.2331 | 0 |  | 3.3571 | 0.2020 | 0 | 2.9556 | 0.2970 | 0 | 2.7350 | \-0.0271 | 1 |
|  | 78 |  | 3.6884 | 0.1930 | 0 | 5.4783 | 0.3447 | 0 | 6.4470 | 0.4454 | 0 |  | 5.5334 | 0.3251 | 0 | 7.0404 | 0.4116 | 0 | 4.4158 | 0.2503 | 0 |  | 3.8241 | 0.2429 | 0 | 3.4005 | 0.3212 | 0 | 3.3081 | \-0.1337 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  | 79 |  | 3.8234 | 0.2251 | 0 | 5.7610 | 0.4048 | 0 | 6.8284 | 0.4707 | 0 |  | 5.8599 | 0.3392 | 0 | 7.2263 | 0.3956 | 0 | 4.6646 | 0.3493 | 0 |  | 4.0534 | 0.3223 | 0 | 3.6003 | 0.3748 | 0 | 3.8562 | \-0.0345 | 1 |
|  | 80 |  | 3.9549 | 0.2345 | 0 | 6 | 0.3577 | 0 | 7.1986 | 0.4754 | 0 |  | 6.1692 | 0.3513 | 0 | 7.4181 | 0.4106 | 0 | 4.7713 | 0.3364 | 0 |  | 4.2201 | 0.3082 | 0 | 3.7534 | 0.3606 | 0 | 4.2202 | \-0.0017 | 1 |
|  | 83 |  | 4.3148 | 0.2917 | 0 | 6.5218 | 0.4124 | 0 | 7.9736 | 0.4780 | 0 |  | 6.8316 | 0.3269 | 0 | 7.3116 | 0.3324 | 0 | 5.4876 | 0.4766 | 0 |  | 4.5474 | 0.3669 | 0 | 3.9718 | 0.2714 | 0 | 6.4005 | \-0.0374 | 1 |
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |

*p	p	p	p	p	p	p	p*

CBD model: Nonlinear variant

Australia	United Kingdom	Italy	France	Spain	New Zealand	Sweden	Germany	Russia

			  
*x*  CapR(%)  ∆*R  j* I*x*(*N* ) CapR(%)  ∆*R  j* I*x*(*N* ) CapR(%)  ∆*R  j* I*x*(*N* ) CapR(%)  ∆*R  j* I*x*(*N* ) CapR(%)  ∆*R  j* I*x*(*N* ) CapR(%)  ∆*R  j* I*x*(*N* ) CapR(%)	∆*R	j* I*x*(*N* )  CapR(%)	∆*R	j* I*x*(*N* )  CapR(%)  ∆*R  j* I*x*(*N* )  
*p	p	p	p	p	p	p	p	p*

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,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>

[image3]: <data:image/png;base64,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>

[image4]: <data:image/png;base64,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>