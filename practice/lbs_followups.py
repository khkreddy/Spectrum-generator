#!/usr/bin/env python3
"""Precomputed learn-by-solve follow-ups. Runtime is a lookup, not a model call.

Each wrong option has a V2 mx type + a follow-up MCQ that zooms onto that
pathway. mx_type is for the teacher key only; the student sees the follow-up
question, never the type name.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "static" / "lbs.json"

TS = "term_substitution"
CO = "condition_omission"
RR = "relationship_reversal"
SE = "scope_error"
SF = "surface_feature_capture"
MC = "mechanism_conflation"
OC = "operation_confusion"


def fu(mx, pathway, stem, a, b, c, d, key, why):
    return {
        "mx_type": mx,
        "pathway": pathway,
        "followup": {
            "stem": stem,
            "options": {"A": a, "B": b, "C": c, "D": d},
            "key": key,
            "why": why,
        },
    }


def item(solve, wrong):
    return {"solve": solve, "wrong": wrong}


# --- shared IR probes ---
OH_ALC = fu(
    CO,
    "Student reads a C=O or fingerprint and names an alcohol, dropping the required broad O–H at 3200–3600 cm⁻¹.",
    "A liquid alcohol IR must show a broad O–H stretch. In which range does that band appear?",
    "1640–1750 cm⁻¹",
    "2200–2250 cm⁻¹",
    "2500–3000 cm⁻¹ (carboxyl canyon)",
    "3200–3600 cm⁻¹",
    "D",
    "Alcohol O–H is 3200–3600 cm⁻¹ and broad. 2500–3000 cm⁻¹ is the carboxylic acid canyon.",
)
OH_ACID = fu(
    CO,
    "Student treats any C=O as a carboxylic acid and omits the very broad 2500–3000 cm⁻¹ O–H canyon.",
    "Which extra feature, besides a C=O near 1700 cm⁻¹, is required before you can call the compound a carboxylic acid?",
    "A sharp peak at 2200–2250 cm⁻¹",
    "A very broad O–H absorption spanning about 2500–3000 cm⁻¹",
    "A sharp peak at 3300–3500 cm⁻¹",
    "No absorption above 1500 cm⁻¹",
    "B",
    "Carboxyl O–H is a canyon from about 2500–3000 cm⁻¹. A ketone has C=O without that canyon.",
)
BOTH_CO_OH = fu(
    CO,
    "Student sees C=O and also names a hydroxyketone/hydroxyaldehyde, omitting that an alcohol O–H would still have to be present.",
    "A molecule with both a ketone C=O and an alcohol O–H must show which pair of bands?",
    "Sharp C=O near 1700 cm⁻¹ only",
    "Broad O–H at 3200–3600 cm⁻¹ only",
    "Both a sharp C=O near 1700 cm⁻¹ and a broad O–H at 3200–3600 cm⁻¹",
    "A nitrile band at 2200–2250 cm⁻¹",
    "C",
    "Both groups are independent absorbers. Missing the alcohol O–H rules out a hydroxyketone.",
)
NO_CN = fu(
    SF,
    "Student maps a weak high-wavenumber wiggle or C–H region onto C≡N because 2200 cm⁻¹ is a memorable number.",
    "A nitrile C≡N stretch, when present, is a weak-to-medium sharp band in which range?",
    "1040–1300 cm⁻¹",
    "1640–1750 cm⁻¹",
    "2200–2250 cm⁻¹",
    "3200–3600 cm⁻¹",
    "C",
    "If that 2200–2250 cm⁻¹ band is absent, the compound is not a nitrile.",
)

KETONE_ID = item(
    "The spectrum has a deep sharp C=O near 1700–1750 cm⁻¹, no broad O–H at 3200–3600 cm⁻¹, and no carboxyl canyon at 2500–3000 cm⁻¹. That is a ketone (propanone), not an acid, alcohol, or hydroxyketone.",
    {
        "A": OH_ACID,
        "B": OH_ALC,
        "D": BOTH_CO_OH,
    },
)

PRIMARY_OL_ID = item(
    "Three carbons, broad alcohol O–H (3200–3600 cm⁻¹), C–O near 1000–1050 cm⁻¹, CH₂ scissor near 1465 cm⁻¹, and no C=O. That is propan-1-ol, not the aldehyde, acid or ester.",
    {
        "A": fu(
            CO,
            "Student expects an aldehyde from a simplified fingerprint and omits the aldehyde C=O (~1730) plus C–H ~2700–2800 cm⁻¹.",
            "Propanal would show a strong C=O. Roughly where?",
            "1040–1300 cm⁻¹",
            "1500–1600 cm⁻¹",
            "1710–1740 cm⁻¹",
            "3200–3600 cm⁻¹",
            "C",
            "No C=O on this spectrum rules out the aldehyde.",
        ),
        "B": OH_ACID,
        "D": fu(
            MC,
            "Student conflates ester C–O with alcohol C–O, ignoring that an ester also has a strong C=O near 1740 cm⁻¹.",
            "An ester such as methyl ethanoate must show which pair?",
            "O–H 3200–3600 cm⁻¹ only",
            "C=O near 1740 cm⁻¹ and C–O near 1050–1250 cm⁻¹",
            "C≡N at 2200 cm⁻¹",
            "Carboxyl canyon 2500–3000 cm⁻¹ only",
            "B",
            "No C=O rules out the ester. Alcohol C–O is not enough.",
        ),
    },
)

ACID_ID = item(
    "Very broad O–H from ~2500–3300 cm⁻¹ plus a sharp C=O near 1710 cm⁻¹ is the carboxyl signature. That is the acid, not the alcohol (O–H higher and no C=O), aldehyde/ketone (C=O, no canyon), or ester (C=O + C–O, no O–H).",
    {
        "A": fu(
            TS,
            "Student swaps carboxyl O–H for alcohol O–H.",
            "Alcohol O–H and carboxyl O–H sit in different ranges. Which pairing is correct?",
            "Alcohol 2500–3000 cm⁻¹; carboxyl 3200–3600 cm⁻¹",
            "Alcohol 3200–3600 cm⁻¹; carboxyl 2500–3000 cm⁻¹",
            "Both 1640–1750 cm⁻¹",
            "Both 2200–2250 cm⁻¹",
            "B",
            "A canyon centred near 3000 cm⁻¹ is carboxyl, not a simple alcohol.",
        ),
        "B": fu(
            CO,
            "Student names the aldehyde from C=O and omits that an aldehyde has no O–H canyon.",
            "If the spectrum shows a very broad O–H spanning 2500–3000 cm⁻¹, can the compound be propanal?",
            "Yes — aldehydes always show that canyon",
            "Yes — that band is aldehyde C–H",
            "No — propanal has C=O but not a carboxyl O–H canyon",
            "No — aldehydes absorb only below 1000 cm⁻¹",
            "C",
            "The canyon is carboxyl O–H. Propanal does not have it.",
        ),
        "D": fu(
            CO,
            "Student names the ketone from C=O and omits the O–H canyon sitting on top of it.",
            "Propanone has a sharp C=O and no O–H. What would you not see for propanone?",
            "A sharp band near 1715 cm⁻¹",
            "Alkyl C–H near 2900 cm⁻¹",
            "A very broad absorption from 2500–3300 cm⁻¹",
            "Fingerprint peaks below 1500 cm⁻¹",
            "C",
            "The broad 2500–3300 cm⁻¹ canyon rules out a simple ketone.",
        ),
    },
)

ACETIC_ID = item(
    "The plotted spectrum is ethanoic acid: carboxyl canyon + C=O. Ethanol has alcohol O–H and no C=O; ethyl ethanoate has C=O + C–O and no O–H; propanone has C=O only.",
    {
        "B": OH_ALC,
        "C": fu(
            MC,
            "Student conflates ester with acid because both have C=O.",
            "Ethyl ethanoate (ester) vs ethanoic acid: which statement is true?",
            "Both show a 2500–3000 cm⁻¹ O–H canyon",
            "The ester has C=O + C–O and no O–H; the acid has C=O + a carboxyl O–H canyon",
            "Neither has a C=O",
            "Only the ester has a C=O",
            "B",
            "No O–H canyon means ester or ketone, not carboxylic acid.",
        ),
        "D": fu(
            CO,
            "Student matches C=O to propanone and omits the carboxyl O–H.",
            "Propanone would lack which of these?",
            "C=O near 1715 cm⁻¹",
            "The 2500–3000 cm⁻¹ O–H canyon",
            "C–H near 2900 cm⁻¹",
            "A fingerprint region",
            "B",
            "The canyon on the plot is not a ketone spectrum.",
        ),
    },
)

ESTER_FG = item(
    "Strong C=O near 1740 cm⁻¹ plus strong C–O near 1240 cm⁻¹, and no O–H above 3100 cm⁻¹: ester, not alcohol, acid, or nitrile.",
    {
        "A": OH_ALC,
        "B": OH_ACID,
        "D": NO_CN,
    },
)

SEC_OL_ID = item(
    "Broad alcohol O–H at 3200–3600 cm⁻¹, no C=O, isopropyl CH₃ ~1375 cm⁻¹ and 2° C–O ~1130 cm⁻¹: propan-2-ol. Ester and aldehyde need C=O; acid needs the carboxyl canyon.",
    {
        "A": fu(
            MC,
            "Student conflates ester C–O with alcohol C–O.",
            "Methyl ethanoate must show a strong C=O. This spectrum has a broad O–H and no C=O. What is ruled out?",
            "An alcohol",
            "An ester",
            "An alkane",
            "Nothing — C–O alone proves an ester",
            "B",
            "Ester = C=O + C–O. Alcohol O–H without C=O is not an ester.",
        ),
        "B": fu(
            CO,
            "Student names the aldehyde from the alkyl region and omits C=O / aldehyde C–H.",
            "Propanal needs a C=O near 1730 cm⁻¹. If that band is absent, is propanal possible?",
            "Yes, if O–H is present",
            "Yes, fingerprint peaks are enough",
            "No — no C=O means it is not an aldehyde",
            "No — aldehydes never show C–H",
            "C",
            "No C=O rules out propanal.",
        ),
        "C": OH_ACID,
    },
)

POLYOL_ID = item(
    "Broad alcohol O–H, C–O, no C=O: glycerol HOCH₂CH(OH)CH₂OH. A and B have C=O (ketone/aldehyde); D has a carboxyl canyon.",
    {
        "A": BOTH_CO_OH,
        "B": BOTH_CO_OH,
        "D": OH_ACID,
    },
)

BANK = {
    "9701_m23_qp_12:q38": KETONE_ID,
    "9701_s18_qp_12:q30": KETONE_ID,
    "9701_s18_qp_11:q30": PRIMARY_OL_ID,
    "9701_s20_qp_13:q25": ACID_ID,
    "9701_s20_qp_11:q29": ACETIC_ID,
    "9701_m24_qp_12:q40": ESTER_FG,
    "9701_w19_qp_11:q30": SEC_OL_ID,
    "9701_w19_qp_13:q30": SEC_OL_ID,
    "9701_w18_qp_12:q30": POLYOL_ID,
    "9701_w23_qp_11:q39": POLYOL_ID,
    "9701_m21_qp_12:q30": item(
        "Spectra: X is an alkene (no C=O, no O–H), Y is a ketone (C=O, no O–H), Z is a carboxylic acid (C=O + carboxyl canyon). Oxidative cleavage of 2-methylpent-2-ene gives propanone + propanoic acid. That is row B.",
        {
            "A": fu(
                CO,
                "Student keeps two ketones and omits that one product spectrum is a carboxylic acid (canyon).",
                "If product Z shows a very broad 2500–3000 cm⁻¹ O–H plus C=O, what functional group is Z?",
                "Ketone",
                "Alcohol",
                "Carboxylic acid",
                "Alkene",
                "C",
                "Two ketones cannot explain an acid spectrum for Z.",
            ),
            "C": fu(
                OC,
                "Student assigns both cleavage fragments as acids, ignoring that a 2,2-disubstituted alkene carbon becomes a ketone.",
                "Oxidative cleavage: a carbon of C=C that bears two alkyl groups and no H becomes which product class?",
                "Carboxylic acid",
                "Ketone",
                "Primary alcohol",
                "Aldehyde that cannot oxidise further",
                "B",
                "Pent-2-ene would not give two acids matching Y (ketone) and Z (acid).",
            ),
            "D": fu(
                MC,
                "Student conflates ester hydrolysis with alkene cleavage.",
                "Hydrolysis of propyl propanoate yields which pair?",
                "Two ketones",
                "An alkene and a ketone",
                "Propan-1-ol and propanoic acid",
                "Two alkenes",
                "C",
                "X would then be an ester (C=O + C–O), not an alkene. The X spectrum is the alkene.",
            ),
        },
    ),
    "9701_m22_qp_12:q40": item(
        "Need both C=O (~1700 cm⁻¹, sharp) and O–H (alcohol 3200–3600 or carboxyl 2500–3000, broad). Diagram B is the only trace that has both.",
        {
            "A": fu(
                CO,
                "Student matches one of the two required groups and omits the other.",
                "A compound with both C=O and O–H must show which pattern?",
                "A sharp ~1700 cm⁻¹ band only",
                "A broad O–H only",
                "A sharp C=O and a broad O–H",
                "A nitrile band only",
                "C",
                "Look again at B: both features are there. The diagram you picked is missing one.",
            ),
            "C": fu(
                SF,
                "Student captures a deep fingerprint trough as if it were O–H or C=O.",
                "O–H stretches live at high wavenumber. Which side of a 4000→500 cm⁻¹ plot is that?",
                "The far right (near 500 cm⁻¹)",
                "The left-hand half (above ~2500 cm⁻¹)",
                "Only the exact centre",
                "O–H never appears on IR plots",
                "B",
                "Do not read a low-wavenumber fingerprint spike as O–H.",
            ),
            "D": fu(
                CO,
                "Student sees C=O and stops, omitting O–H.",
                "Which one feature is not enough to claim ‘both C=O and O–H’?",
                "A carboxyl canyon plus C=O",
                "Alcohol O–H plus C=O",
                "A sharp C=O with a flat 2500–3600 cm⁻¹ region",
                "Acid O–H plus C=O",
                "C",
                "C=O alone is a ketone or ester, not ‘both C=O and O–H’.",
            ),
        },
    ),
    "9701_s19_qp_11:q24": item(
        "Empirical formula C₂H₄O. Peak X is in the C–H stretch region (~2900); peak Y is the C=O (~1700). That is ethanal (or similar). Not O–H (no broad high-ν band) and not C=C as the strong Y.",
        {
            "A": fu(
                TS,
                "Student substitutes C=C for C=O at ~1700 cm⁻¹.",
                "A strong sharp band near 1700 cm⁻¹ is which bond in this table?",
                "C=C (1500–1680 cm⁻¹, usually weaker)",
                "C=O (1670–1750 cm⁻¹)",
                "C≡N (2200–2250 cm⁻¹)",
                "O–H (3200–3600 cm⁻¹)",
                "B",
                "Y is the carbonyl, not C=C.",
            ),
            "C": fu(
                TS,
                "Student labels a C–H stretch as O–H.",
                "O–H (alcohol) is broad and sits at 3200–3600 cm⁻¹. A sharper band near 2900 cm⁻¹ is usually which bond?",
                "O–H",
                "C=O",
                "C–H",
                "C≡N",
                "C",
                "X is C–H, not O–H. There is no broad alcohol band.",
            ),
            "D": fu(
                CO,
                "Student assigns O–H and C=O as if the molecule were a carboxylic acid, omitting that X is not a canyon.",
                "Carboxyl O–H is a very broad canyon at 2500–3000 cm⁻¹. If peak X is a relatively sharp band near 2900 cm⁻¹, is it carboxyl O–H?",
                "Yes, all bands near 2900 cm⁻¹ are O–H",
                "No — that shape and position are C–H",
                "Yes, if a C=O is also present",
                "No — carboxyl O–H is at 2200 cm⁻¹",
                "B",
                "C₂H₄O with C–H + C=O is the aldehyde, not the acid.",
            ),
        },
    ),
    "9701_s19_qp_12:q30": item(
        "Q shows C=O and no O–H: butanone. Butan-1-ol has alcohol O–H; butanoic acid has the canyon; 3-hydroxybutanal has both C=O and O–H.",
        {
            "A": OH_ALC,
            "B": OH_ACID,
            "D": BOTH_CO_OH,
        },
    ),
    "9701_s19_qp_13:q40": item(
        "C₅H₁₀O₂, strong 1250 cm⁻¹ (C–O), strong 1720 cm⁻¹ (C=O), no strong peak above 3100 cm⁻¹ (no O–H). Ethyl propanoate and methyl butanoate are esters that fit. 1-hydroxypentan-3-one has an alcohol O–H above 3100 cm⁻¹, so 3 is out. Key B (1 and 2 only).",
        {
            "A": fu(
                CO,
                "Student includes the hydroxyketone and omits the ‘no peak above 3100 cm⁻¹’ condition.",
                "A strong peak above 3100 cm⁻¹ in this context is which group?",
                "Ester C=O",
                "Alcohol O–H",
                "C–H of CH₃ only",
                "C–O of an ester",
                "B",
                "Statement 3 has an alcohol, which would absorb above 3100 cm⁻¹. It is out.",
            ),
            "C": fu(
                SE,
                "Student drops ethyl propanoate for no chemical reason (scope under-extended).",
                "Ethyl propanoate is C₅H₁₀O₂ and is an ester. Should it show C=O ~1720 and C–O ~1250 with no O–H?",
                "No, esters have O–H",
                "Yes",
                "No, esters have no C=O",
                "Only methyl esters do",
                "B",
                "Both isomeric esters fit. Do not drop statement 1.",
            ),
            "D": fu(
                SE,
                "Student keeps only one ester and under-extends the same argument to the other isomer.",
                "Methyl butanoate and ethyl propanoate are isomers. Do they share the same IR functional-group pattern?",
                "No — only ethyl esters show C=O",
                "No — only methyl esters show C–O",
                "Yes — both are esters: C=O + C–O, no O–H",
                "Yes — both are alcohols",
                "C",
                "Both 1 and 2 are correct.",
            ),
        },
    ),
    "9701_s20_qp_12:q21": item(
        "P is CH₄O = methanol (alcohol, no C=O). Q is CH₂O₂ = methanoic acid (C=O). R is CH₂O = methanal (C=O). Strong 1610–1750 cm⁻¹ is C=O, so Q and R only.",
        {
            "A": fu(
                CO,
                "Student omits methanal’s C=O.",
                "Methanal (CH₂O) is an aldehyde. Does it have a C=O absorption in 1610–1750 cm⁻¹?",
                "No, aldehydes have no C=O",
                "Yes",
                "Only if an O–H is also present",
                "Only in the fingerprint region",
                "B",
                "R belongs with Q. The answer is Q and R.",
            ),
            "B": fu(
                CO,
                "Student omits the acid’s C=O.",
                "Methanoic acid (CH₂O₂) contains which bond that absorbs at 1610–1750 cm⁻¹?",
                "O–H only",
                "C=O",
                "C≡N",
                "None — acids are silent there",
                "B",
                "Q has C=O as well. Not R only.",
            ),
            "D": fu(
                SE,
                "Student over-extends C=O to methanol because it contains oxygen.",
                "Methanol is CH₃OH. Does it have a C=O?",
                "Yes, all oxygen compounds have C=O",
                "Yes, at 3200 cm⁻¹",
                "No — it has C–O and O–H, not C=O",
                "No — methanol is an alkane",
                "C",
                "P does not absorb as a carbonyl. Not all three.",
            ),
        },
    ),
    "9701_s20_qp_12:q38": item(
        "Propanal + HCN → 2-hydroxybutanenitrile (cyanohydrin): C≡N (2200–2250, weak), alcohol O–H (3200–3600, strong), C–O (1040–1300, strong). All three. The aldehyde C=O is gone.",
        {
            "B": fu(
                CO,
                "Student omits the new C–O of the alcohol.",
                "The cyanohydrin has a C–OH group. Does that add a strong 1040–1300 cm⁻¹ C–O band?",
                "No, only O–H appears",
                "Yes",
                "Only if the C≡N is absent",
                "C–O appears at 2200 cm⁻¹",
                "B",
                "Statement 3 is true as well. All three.",
            ),
            "C": fu(
                CO,
                "Student omits the nitrile that was just added.",
                "HCN adds a C≡N. Where does that weak band sit?",
                "1040–1300 cm⁻¹",
                "1640–1750 cm⁻¹",
                "2200–2250 cm⁻¹",
                "3200–3600 cm⁻¹",
                "C",
                "Statement 1 is true. All three bands are present.",
            ),
            "D": fu(
                SE,
                "Student keeps only the nitrile and drops alcohol bands.",
                "The product is a cyanohydrin (HO–C–C≡N). Which groups are present?",
                "C≡N only",
                "O–H and C–O only",
                "C≡N, O–H and C–O",
                "C=O only",
                "C",
                "All three listed absorptions are present.",
            ),
        },
    ),
    "9701_s21_qp_11:q26": item(
        "Empirical C₂H₄O, IR of an ester (C=O ~1740, C–O ~1240, no O–H): ethyl ethanoate. Cyclic ester would fit IR but the question asks the skeletal formula that matches this acyclic ester. C and D have O–H (and C has C=C).",
        {
            "B": fu(
                SE,
                "Student over-extends ‘ester IR’ to a cyclic ester that is not the molecule implied by the plotted (ethyl ethanoate) pattern / formula pairing used here.",
                "C₂H₄O for ethyl ethanoate is the empirical formula of C₄H₈O₂. A C₄ cyclic ester is an isomer. What extra check still favours ethyl ethanoate on a typical 9701 ester plot?",
                "Cyclic esters have O–H",
                "The acyclic acetate pattern (C=O + C–O, no O–H) plus the usual teaching example",
                "Cyclic esters have C≡N",
                "Empirical formula forbids C₄ esters",
                "B",
                "The intended structure is ethyl ethanoate, not the lactone.",
            ),
            "C": BOTH_CO_OH,
            "D": BOTH_CO_OH,
        },
    ),
    "9701_s21_qp_12:q30": item(
        "C₄H₈O. IR shows alcohol O–H and C=C (~1640), not C=O and not a carboxyl canyon. Butanoic acid is C₄H₈O₂ (wrong formula) and would show the canyon. Butanone has C=O, no O–H. Cyclobutanol has O–H but no C=C. But-3-en-1-ol fits.",
        {
            "A": fu(
                CO,
                "Student matches a ketone to C₄H₈O and omits the O–H on the left of the plot.",
                "The O–H absorption on the left of the spectrum rules out which class?",
                "Alcohols",
                "Carboxylic acids",
                "Ketones such as butanone",
                "Alkenes that also contain O–H",
                "C",
                "Butanone has no O–H. Examiner: O–H rules out A.",
            ),
            "B": fu(
                CO,
                "Student keeps a cyclic alcohol and omits the C=C band at 1600–1700 cm⁻¹.",
                "A band between 1600 and 1700 cm⁻¹ on this plot (with O–H, no C=O) is which bond?",
                "C=O of a ketone",
                "C=C of an alkene",
                "C≡N",
                "C–O of an ether only",
                "B",
                "C=C means D, not cyclobutanol. Examiner comment matches this.",
            ),
            "C": fu(
                SE,
                "Student ignores the given molecular formula and names butanoic acid from an O–H shape.",
                "Butanoic acid is C₄H₈O₂. Z is C₄H₈O. Can Z be butanoic acid?",
                "Yes, IR overrides molecular formula",
                "Yes, acids are always C₄H₈O",
                "No — the formula does not match",
                "No — acids have no O–H",
                "C",
                "Examiner: C is the most common wrong answer; the formula already kills it.",
            ),
        },
    ),
    "9701_s21_qp_13:q30": item(
        "The IR has neither aldehyde C=O, nor carboxyl canyon, nor alcohol O–H: two ether-like C–O environments. 2,5-bis(methoxymethyl)furan. A has OH+CHO, B two CO₂H, C has CHO.",
        {
            "A": BOTH_CO_OH,
            "B": OH_ACID,
            "C": fu(
                CO,
                "Student keeps the aldehyde and omits the missing C=O.",
                "An aldehyde substituent requires a C=O near 1700 cm⁻¹. If that band is absent, which structures die?",
                "Only the diacid",
                "Any structure that still carries –CHO",
                "Only ethers",
                "None",
                "B",
                "C still has –CHO. D has only ether linkages.",
            ),
        },
    ),
    "9701_s24_qp_12:q40": item(
        "X is oxidised by acidified dichromate to Y. Y’s IR is a carboxylic acid (canyon + C=O). Primary alcohol → acid under reflux with excess oxidant. X is propan-1-ol. Propan-2-ol would give a ketone; propanone does not oxidise; propanoic acid is already Y, not X.",
        {
            "B": fu(
                MC,
                "Student conflates 2° oxidation (ketone) with 1° oxidation (acid).",
                "Excess hot acidified dichromate: what is the organic product from propan-2-ol?",
                "Propanoic acid",
                "Propanone",
                "Propanal",
                "No reaction? it already is an acid",
                "B",
                "Y is an acid, so X was the primary alcohol, not propan-2-ol.",
            ),
            "C": fu(
                CO,
                "Student omits that ketones are not oxidised by this reagent.",
                "Does propanone react with acidified K₂Cr₂O₇ to give a carboxylic acid?",
                "Yes, all carbonyls oxidise to acids",
                "No — ketones are not oxidised under these conditions",
                "Yes, to propan-1-ol",
                "Yes, to an alkene",
                "B",
                "X cannot already be the ketone if Y is a new oxidation product that is an acid.",
            ),
            "D": fu(
                RR,
                "Student reverses X and Y: the acid is the product, not the starting alcohol.",
                "The question asks for X, the reactant. Y is the oxidation product whose IR is shown. If Y is propanoic acid, what is X?",
                "Propanoic acid",
                "Propanone",
                "Propan-1-ol (oxidised all the way to the acid)",
                "An alkene",
                "C",
                "D is Y, not X.",
            ),
        },
    ),
    "9701_s24_qp_13:q40": item(
        "But-2-enoic acid. Broad 2500–3000 cm⁻¹ is carboxyl O–H, not C=C, C=O, or C–O.",
        {
            "A": fu(
                TS,
                "Student substitutes C=C for the broad 2500–3000 cm⁻¹ band.",
                "C=C absorbs at 1500–1680 cm⁻¹. The broad 2500–3000 cm⁻¹ peak is which bond of the acid?",
                "C=C",
                "O–H (carboxyl)",
                "C≡N",
                "N–H",
                "B",
                "The table assigns 2500–3000 cm⁻¹ to carboxyl O–H.",
            ),
            "B": fu(
                TS,
                "Student substitutes C=O for the broad high-wavenumber canyon.",
                "C=O is a sharp band at 1670–1750 cm⁻¹. A broad 2500–3000 cm⁻¹ peak is not C=O. What is it?",
                "C=O nonetheless",
                "C–O",
                "Carboxyl O–H",
                "C=C",
                "C",
                "Shape (broad) and range both say O–H, not C=O.",
            ),
            "C": fu(
                SF,
                "Student captures ‘the molecule contains C–O’ and maps it onto the wrong peak.",
                "C–O of an acid/ester is 1040–1300 cm⁻¹. The 2500–3000 cm⁻¹ broad peak is which bond?",
                "C–O",
                "C=C",
                "C=O",
                "O–H",
                "D",
                "Right molecule, wrong bond for this peak.",
            ),
        },
    ),
    "9701_w18_qp_11:q30": item(
        "K’s IR is C=O without a carboxyl canyon, so aldehyde or ketone. Excess reflux dichromate would oxidise an aldehyde on to an acid, and the question says good yield of K — so K is a ketone and J a secondary alcohol. J is branched C₅H₁₂O. B is unbranched. C fits. Examiner: D was the common error (acid).",
        {
            "A": fu(
                CO,
                "Student stops at aldehyde and omits that excess reflux dichromate oxidises aldehydes to acids.",
                "Under the stated conditions (excess Cr₂O₇²⁻/H⁺, heat, until no further reaction), what happens to an aldehyde?",
                "It is the final product",
                "It is oxidised on to a carboxylic acid",
                "It is reduced to a primary alcohol",
                "It is unchanged",
                "B",
                "K cannot be the aldehyde. Examiner used this to kill A.",
            ),
            "B": fu(
                CO,
                "Student picks a secondary alcohol → ketone pair but omits ‘branched-chain’.",
                "J is stated to be a branched-chain alcohol. Is pentan-3-ol branched?",
                "Yes, any secondary alcohol is branched",
                "No — CH₃CH₂CH(OH)CH₂CH₃ is a straight chain",
                "Yes, because it has five carbons",
                "No, because ketones cannot be branched",
                "B",
                "B is the right chemistry on the wrong skeleton.",
            ),
            "D": fu(
                MC,
                "Student conflates the acid product of a primary alcohol with the ketone actually on the IR.",
                "K’s IR shows C=O but no COOH canyon. What is K?",
                "Carboxylic acid",
                "Ketone (or aldehyde, but aldehyde would not survive these conditions)",
                "Alcohol",
                "Alkene",
                "B",
                "Examiner: D was the most common wrong answer; the canyon is missing.",
            ),
        },
    ),
    "9701_w19_qp_12:q30": item(
        "C 62.07%, H 10.34%, O 27.59% → C₆H₁₂O₂. IR is alcohol O–H, no C=O: a diol. Cyclohexane-1,4-diol is C₆H₁₂O₂. Pentane-1,5-diol is C₅H₁₂O₂. The acid has C=O+canyon; propanone is C₃H₆O with C=O.",
        {
            "B": fu(
                CO,
                "Student matches composition loosely and omits that the IR has no carboxyl C=O/canyon.",
                "3-methylpentanoic acid has C=O and carboxyl O–H. If the IR is an alcohol without C=O, is the acid possible?",
                "Yes",
                "No",
                "Yes, if the percentages match",
                "Yes, acids never show C=O",
                "B",
                "IR already kills the acid.",
            ),
            "C": fu(
                SE,
                "Student recognises a ketone IR in memory and ignores both composition and the O–H on the plot.",
                "Propanone is C₃H₆O. Does 62% C / 27% O match C₃H₆O?",
                "Yes",
                "No — propanone is far too small and would show C=O, not alcohol O–H",
                "Yes if you ignore hydrogen",
                "Yes, all ketones are C₆H₁₂O₂",
                "B",
                "Wrong formula and wrong functional group.",
            ),
            "D": fu(
                OC,
                "Student gets ‘diol, no C=O’ and then fails the empirical-formula arithmetic (C₅ vs C₆).",
                "Pentane-1,5-diol is C₅H₁₂O₂ (O = 32/104 ≈ 30.8%). The data are O = 27.59%. Which diol matches C₆H₁₂O₂ (O = 32/116 ≈ 27.6%)?",
                "Pentane-1,5-diol",
                "Cyclohexane-1,4-diol",
                "Propanone",
                "Any C₅ acid",
                "B",
                "Right functional group, wrong carbon count.",
            ),
        },
    ),
    "9701_w20_qp_11:q37": item(
        "From the structure, Mᵣ = 116 (statement 1). Two carbonyl groups → two strong 1640–1740 cm⁻¹ bands (statement 2). 2500–3000 cm⁻¹ is not ‘only a sharp C–H’: a carboxyl O–H canyon is there, so 3 is false. Key B.",
        {
            "A": fu(
                TS,
                "Student treats the carboxyl O–H canyon as a sharp C–H and admits statement 3.",
                "A sharp strong band near 2900 cm⁻¹ is C–H. A very broad 2500–3000 cm⁻¹ absorption is which bond?",
                "C–H as well",
                "Carboxyl O–H",
                "C≡N",
                "C=C",
                "B",
                "Statement 3 is false, so not ‘all three’.",
            ),
            "C": fu(
                OC,
                "Student drops the Mᵣ count (operation on the structure).",
                "Mᵣ is the sum of the atomic masses on the displayed structure. If that sum is 116, is statement 1 true?",
                "No, Mᵣ cannot be read from a structure",
                "Yes",
                "Only if the IR agrees",
                "Only for hydrocarbons",
                "B",
                "1 and 2 are both true.",
            ),
            "D": fu(
                CO,
                "Student omits the two carbonyls in 1640–1740 cm⁻¹.",
                "Two separate C=O groups each absorb in 1640–1740 cm⁻¹. Does that make statement 2 true?",
                "No, only one C=O ever appears",
                "Yes",
                "No, C=O is at 3200 cm⁻¹",
                "Only for ketones, never acids/esters",
                "B",
                "Do not drop statement 2.",
            ),
        },
    ),
    "9701_w21_qp_11:q30": item(
        "Spectrum 1: C=O, no O–H → ketone (propanone). Spectrum 2: C=O + carboxyl canyon → propanoic acid. Spectrum 3: alcohol O–H, no C=O → propan-2-ol. Row B.",
        {
            "A": fu(
                RR,
                "Student reverses ketone and acid on spectra 1 and 2.",
                "Which spectrum is the carboxylic acid?",
                "The one with C=O only",
                "The one with C=O plus a 2500–3000 cm⁻¹ canyon",
                "The one with only alcohol O–H",
                "None of them",
                "B",
                "That is spectrum 2, not spectrum 1.",
            ),
            "C": fu(
                RR,
                "Student swaps the acid and the alcohol.",
                "Alcohol vs acid: which has the 2500–3000 cm⁻¹ canyon?",
                "The alcohol",
                "The carboxylic acid",
                "The ketone",
                "Both equally",
                "B",
                "Spectrum 3 is the alcohol; spectrum 2 is the acid.",
            ),
            "D": fu(
                RR,
                "Student reverses the whole assignment (alcohol as spectrum 1).",
                "A plot with no O–H and a sharp C=O is which of these three?",
                "Propan-2-ol",
                "Propanoic acid",
                "Propanone",
                "None",
                "C",
                "Spectrum 1 is the ketone, so D is backwards.",
            ),
        },
    ),
    "9701_w21_qp_12:q30": item(
        "Y shows alcohol O–H and C=C, no C=O: HOCH₂CH=CHCH₂OH. Ester has C=O+C–O; acid has canyon+C=O; hydroxyaldehyde has C=O+O–H.",
        {
            "A": fu(
                MC,
                "Student conflates ester with the unsaturated diol.",
                "Ethyl ethanoate has no O–H. If Y shows alcohol O–H, can it be the ester?",
                "Yes",
                "No",
                "Yes, esters always show O–H",
                "Yes, if C=C is present",
                "B",
                "O–H on the plot kills the ester.",
            ),
            "C": OH_ACID,
            "D": BOTH_CO_OH,
        },
    ),
    "9701_w22_qp_12:q40": item(
        "P has three carbons and C=O at 1720 cm⁻¹. Excess hot dichromate gives Q with C=O ~1700 and a broad 2800 cm⁻¹ carboxyl O–H: Q is the acid, so P was the aldehyde (propanal). Ketones and 2° alcohols give ketones that do not become acids; 1° alcohol P would not itself show 1720 cm⁻¹ C=O.",
        {
            "B": fu(
                CO,
                "Student starts from ‘C=O at 1720’ and omits that the ketone would not oxidise to an acid.",
                "Propanone has C=O. Does excess hot dichromate turn it into a carboxylic acid?",
                "Yes",
                "No",
                "Yes, always",
                "Yes, to propan-1-ol first",
                "B",
                "Q is an acid, so P was oxidisable at the carbonyl carbon — the aldehyde.",
            ),
            "C": fu(
                CO,
                "Student picks the primary alcohol that can become the acid, omitting that P itself already has C=O at 1720 cm⁻¹.",
                "Propan-1-ol’s IR has O–H, not a strong 1720 cm⁻¹ C=O. Does P (strong 1720 cm⁻¹) match propan-1-ol?",
                "Yes",
                "No — P already contains C=O, so it is not the alcohol",
                "Yes, alcohols always show 1720 cm⁻¹",
                "Yes, because it oxidises to an acid",
                "B",
                "Right oxidation story, wrong starting functional group.",
            ),
            "D": fu(
                MC,
                "Student conflates 2° alcohol (oxidises to ketone) with the aldehyde that oxidises to the acid Q.",
                "Propan-2-ol oxidises to propanone, which then stops. Can Q (a carboxylic acid) come from propan-2-ol?",
                "Yes",
                "No",
                "Yes, via propanal",
                "Yes, all C₃ alcohols give propanoic acid",
                "B",
                "Only the aldehyde (or 1° alcohol) yields the acid. P’s own C=O picks the aldehyde.",
            ),
        },
    ),
}

# clones that share the hinge
BANK["9701_w18_qp_13:q30"] = BANK["9701_w18_qp_11:q30"]
BANK["9701_w20_qp_13:q37"] = BANK["9701_w20_qp_11:q37"]
BANK["9701_w21_qp_13:q30"] = BANK["9701_w21_qp_11:q30"]

# --- mass spectrometry ---
BANK["9701_s02_qp_1:q3"] = item(
    "A_r = (63×7 + 65×3) / (7+3) = (441+195)/10 = 63.6.",
    {
        "A": fu(
            OC,
            "Student used a one-sided or truncated weighted mean (e.g. 63 + 0.3).",
            "Copper peaks at 63 (abundance 7) and 65 (abundance 3). What is the correct expression for A_r?",
            "(63+65)/2",
            "63 + 3/10",
            "(63×7 + 65×3)/(7+3)",
            "63×65 / 10",
            "C",
            "Weight each mass by its abundance, then divide by total abundance.",
        ),
        "B": fu(
            OC,
            "Student took the simple mean of 63 and 65.",
            "Why is (63+65)/2 = 64 not the relative atomic mass here?",
            "It is correct",
            "The isotopes are not equally abundant (7 vs 3)",
            "Copper has only one isotope",
            "Mass numbers cannot be averaged",
            "B",
            "63.5 would be the unweighted mean of the mass numbers, not this sample.",
        ),
        "D": fu(
            OC,
            "Student averaged mass numbers as 64.0, ignoring abundances.",
            "If you ignore abundances and average 63 and 65 you get 64.0. What did you fail to use?",
            "The peak heights 7 and 3",
            "The speed of light",
            "The C=O IR table",
            "Avogadro’s number",
            "A",
            "Abundances 7:3 pull A_r toward 63, giving 63.6.",
        ),
    },
)
BANK["9701_s17_qp_11:q2"] = item(
    "A_r = (6×7.42 + 7×92.58)/100 = (44.52 + 648.06)/100 = 6.9258 → 6.93 (3 s.f.).",
    {
        "A": fu(
            RR,
            "Student reversed the abundances onto the other isotope (weighted toward 6).",
            "⁷Li is 92.58% of the sample. Should A_r sit near 6 or near 7?",
            "Near 6",
            "Near 7",
            "Exactly 6.50",
            "Exactly 13",
            "B",
            "6.07 would mean almost pure ⁶Li. The sample is almost all ⁷Li.",
        ),
        "B": fu(
            OC,
            "Student took the unweighted mean of 6 and 7.",
            "(6+7)/2 = 6.50. Why is that wrong?",
            "It is right",
            "The isotopes are 7.42% and 92.58%, not 50:50",
            "You should add 6 and 7",
            "You should divide by 7.42",
            "B",
            "Always weight by the given percentages.",
        ),
        "C": fu(
            OC,
            "Student rounded 6.9258 to 6.90 (wrong s.f. / truncation).",
            "6.9258 to three significant figures is which value?",
            "6.90",
            "6.93",
            "6.9",
            "7.00",
            "B",
            "The third significant figure rounds up: 6.93.",
        ),
    },
)
BANK["9701_s19_qp_11:q2"] = item(
    "Read peak m/e and heights off the figure; A_r = Σ(m×I)/ΣI. The arithmetic gives 114.4.",
    {
        "A": fu(
            OC,
            "Student omitted a peak or used integer masses only.",
            "If several isotope peaks are drawn, which must enter A_r?",
            "Only the tallest peak",
            "Every peak’s (m/e × relative abundance), then divide by total abundance",
            "Only the smallest m/e",
            "The difference between peaks",
            "B",
            "Leaving a peak out pulls the answer down to 113.7.",
        ),
        "B": fu(
            OC,
            "Student rounded mid-way or used unweighted mean of visible masses.",
            "An unweighted mean of nearby mass numbers is not A_r. What weighting is required?",
            "Equal weights",
            "Each mass × its peak height, divided by the sum of heights",
            "Masses squared",
            "Only M+1",
            "B",
            "114.0 is a rounded/unweighted trap.",
        ),
        "C": fu(
            OC,
            "Student dropped the last digit of a correct weighted mean.",
            "If the weighted mean is 114.36, the value to 1 d.p. matching the options is?",
            "113.7",
            "114.0",
            "114.2",
            "114.4",
            "D",
            "Carry the arithmetic through; do not truncate to 114.2.",
        ),
    },
)
BANK["9701_s20_qp_13:q7"] = item(
    "A_r = (32×95.02 + 33×0.76 + 34×4.20 + 36×0.02)/100 = 32.0866 → 32.09 to 4 s.f.",
    {
        "A": fu(
            OC,
            "Student dropped the 36 or 33 term.",
            "Which peaks must be included?",
            "Only m/e 32",
            "32, 33, 34 and 36, each × abundance",
            "Only even m/e",
            "Only the two largest",
            "B",
            "Dropping a term gives 32.07.",
        ),
        "B": fu(
            OC,
            "Student rounded 32.0866 to 32.08 (truncation).",
            "32.0866 to four significant figures is?",
            "32.08",
            "32.09",
            "32.10",
            "32.0",
            "B",
            "The fourth s.f. rounds 8→9 because the next digit is 6.",
        ),
        "D": fu(
            OC,
            "Student rounded the other way to 32.10.",
            "32.0866 is closer to which 4 s.f. value?",
            "32.10",
            "32.09",
            "33.00",
            "32",
            "B",
            "32.10 would require 32.096 or more.",
        ),
    },
)
BANK["9701_s23_qp_13:q40"] = item(
    "M and M+2 equal height → bromine (1:1), not chlorine (3:1). M is 15× (M+1) so n_C ≈ 100/(1.1×15) ≈ 6.06 → six carbons. 3-bromo-2,2-dimethylbutane. Examiner: C was the common error (bromo but seven carbons).",
    {
        "A": fu(
            TS,
            "Student substitutes chlorine for bromine despite equal M and M+2.",
            "Equal M and M+2 heights mean which halogen?",
            "Chlorine (3:1)",
            "Bromine (1:1)",
            "Fluorine (no M+2)",
            "Iodine (no M+2 pair of this kind)",
            "B",
            "A and B are chloro compounds and are out.",
        ),
        "B": fu(
            TS,
            "Same chlorine/bromine swap on a different chloro isomer.",
            "³⁵Cl:³⁷Cl ≈ 3:1, so M:M+2 ≈ 3:1. This spectrum has M:M+2 = 1:1. Halogen?",
            "Cl",
            "Br",
            "F",
            "N",
            "B",
            "Not a chloroalkane.",
        ),
        "C": fu(
            OC,
            "Student got bromine but used the wrong n_C from the M+1 ratio.",
            "M is 15 times M+1. n_C ≈ 100 / (1.1 × 15). That is about how many carbons?",
            "15",
            "7",
            "6",
            "4",
            "C",
            "Examiner: 100/(1.1×15) ≈ 6.06, so D not C.",
        ),
    },
)
BANK["9701_s25_qp_12:q40"] = item(
    "CH₃Cl: M at 50 is ¹²C¹H₃³⁵Cl. M+2 at 52 is ³⁷Cl. ³⁵Cl:³⁷Cl = 3:1, so abundance at 52 = 18.0% × 1/3 = 6.0%.",
    {
        "A": fu(
            OC,
            "Student used 1/4 (perhaps ¹²C/¹³C logic) on the chlorine pair.",
            "³⁵Cl:³⁷Cl ≈ 3:1. If M (³⁵Cl) is 18.0%, M+2 (³⁷Cl) is?",
            "18.0 × 1/4 = 4.5%",
            "18.0 × 1/3 = 6.0%",
            "18.0%",
            "18.0 × 3 = 54%",
            "B",
            "The chlorine isotope ratio is 3:1, not 4:1.",
        ),
        "C": fu(
            RR,
            "Student set M+2 equal to M, as if bromine.",
            "Equal M and M+2 is the bromine pattern. Chlorine is 3:1. Should m/e 52 equal 18.0%?",
            "Yes",
            "No — it should be one-third of 18.0%",
            "Yes, because ³⁷Cl is as common as ³⁵Cl",
            "Yes, because of ¹³C",
            "B",
            "Do not import the bromine 1:1 ratio.",
        ),
        "D": fu(
            RR,
            "Student reversed 3:1 and made M+2 three times M.",
            "3:1 means the lighter chlorine is more abundant. M+2 should be smaller or larger than 18%?",
            "Larger (54%)",
            "Smaller (6%)",
            "Equal",
            "Zero",
            "B",
            "³⁷Cl is the minor isotope.",
        ),
    },
)
BANK["9701_w04_qp_1:q2"] = item(
    "Read the zinc isotope peaks off the figure; A_r = Σ(m×I)/ΣI = 65.5.",
    {
        "A": fu(
            SF,
            "Student reported the nearest mass number of a tall peak instead of the weighted mean.",
            "A_r of an isotopic mixture is which quantity?",
            "The mass number of the tallest peak",
            "The abundance-weighted mean of the peak m/e values",
            "The highest m/e on the plot",
            "Always an integer",
            "B",
            "65 is a mass number, not this sample’s A_r.",
        ),
        "B": fu(
            OC,
            "Student used a partially weighted or two-peak-only mean.",
            "If three zinc isotopes are present, which enter the mean?",
            "Only two of them",
            "All of them, weighted by the printed abundances",
            "Only ⁶⁴Zn",
            "None — use 65.25 from a data book",
            "B",
            "65.25 is a truncated/partial mean.",
        ),
        "D": fu(
            OC,
            "Student over-precise or included an M+1 ¹³C-style term that does not belong on an elemental Zn spectrum.",
            "Elemental zinc’s A_r from the drawn peaks, to the precision of the options, is 65.5. 65.66 usually means which mistake?",
            "Correct extra significant figures from the figure",
            "Carrying a calculator artefact or an extra peak that is not an isotope of Zn",
            "Always how A_r is reported",
            "Ignoring abundances",
            "B",
            "Stay with the weighted mean of the drawn Zn peaks: 65.5.",
        ),
    },
)
BANK["9701_w21_qp_11:q1"] = item(
    "A_r = (20×100 + 21×0.3 + 22×8) / 108.3 = 2182.3 / 108.3 = 20.15. Examiner: D (21.82) was common — forgot to divide by total abundance.",
    {
        "B": fu(
            OC,
            "Student used 108 or 110 as the denominator, or rounded early.",
            "Total abundance is 100+0.3+8 = 108.3. The numerator is 2182.3. 2182.3/108.3 is?",
            "20.15",
            "20.20",
            "21.00",
            "21.82",
            "A",
            "Do not replace 108.3 by 100 or 108.",
        ),
        "C": fu(
            SF,
            "Student picked a visible mass number (21) instead of the weighted mean.",
            "The middle peak is at m/z 21 with height 0.3. Is A_r equal to 21?",
            "Yes, the middle peak is the average",
            "No — 21 is almost absent; A_r sits near 20",
            "Yes, always the median m/z",
            "Yes, because 20, 21, 22 average to 21",
            "B",
            "The sample is almost all ²⁰Ne.",
        ),
        "D": fu(
            OC,
            "Student computed the numerator 20×100+21×0.3+22×8 = 2182.3 and then divided by 100 (or forgot to divide).",
            "After summing m×abundance you must divide by the total abundance 108.3, not by 100. 2182.3/100 = 21.82 is which error?",
            "The correct A_r",
            "Forgetting that the abundances add to 108.3, not 100",
            "Using the wrong neon isotopes",
            "A data-book value",
            "B",
            "Examiner: D was the most common wrong answer.",
        ),
    },
)
BANK["9701_w21_qp_13:q1"] = BANK["9701_w21_qp_11:q1"]

BANK["9701_w24_qp_11:q40"] = item(
    "Cl₂ MS: atomic A_r uses the two atomic peaks (³⁵Cl, ³⁷Cl) — statement 1. Peak Z is Cl₂ molecular ion of the heaviest isotopologue (74); 37.0 g of that species is 0.5 mol of Cl₂ molecules → 0.5×6.02×10²³ = 3.01×10²³ molecules — statement 2. Molecular M_r of Cl₂ uses the three Cl₂ peaks X,Y,Z — statement 3. All three.",
    {
        "B": fu(
            CO,
            "Student omits that M_r(Cl₂) is obtained from the molecular-ion cluster X,Y,Z.",
            "The relative molecular mass of Cl₂ comes from which peaks?",
            "Only the atomic ³⁵Cl peak",
            "The Cl₂ molecular ions (the three peaks around 70–74)",
            "Any two peaks at random",
            "The baseline",
            "B",
            "Statement 3 is true. All three statements hold.",
        ),
        "C": fu(
            CO,
            "Student omits the amount-of-substance reading of peak Z.",
            "If Z is ³⁷Cl–³⁷Cl (M_r 74) but the option uses 37.0 g, that is 0.5 mol of Cl₂. Number of molecules?",
            "6.02×10²³",
            "3.01×10²³",
            "1",
            "37",
            "B",
            "Statement 2 is true.",
        ),
        "D": fu(
            CO,
            "Student drops statement 1 (atomic A_r from two atomic peaks).",
            "A_r of chlorine uses the abundances and m/e of the two atomic isotope peaks. Is that two of the five labelled peaks?",
            "No, you need all five",
            "Yes",
            "No, A_r cannot be measured by MS",
            "No, you need NMR",
            "B",
            "Statement 1 is true. All three.",
        ),
    },
)
BANK["9701_w24_qp_13:q40"] = BANK["9701_w24_qp_11:q40"]

BANK["9701_w24_qp_12:q40"] = item(
    "M+1 / M ≈ 1.1% × n_C. Vitamin C is C₆H₈O₆ so n_C = 6. M+1 abundance = 7.0% × 6 × 0.011 = 0.462%.",
    {
        "B": fu(
            OC,
            "Student used n_C = 7 (counted an oxygen or used C₆H₈O₆ atoms wrongly).",
            "Vitamin C is C₆H₈O₆. How many carbon atoms enter the M+1 (¹³C) calculation?",
            "8",
            "6",
            "12",
            "1",
            "B",
            "7.0 × 7 × 0.011 = 0.539 is the n_C = 7 trap.",
        ),
        "C": fu(
            OC,
            "Student used n_C = 8 (the hydrogens).",
            "M+1 from ¹³C scales with the number of carbons, not hydrogens. n_H = 8 would give 7.0×8×0.011 = 0.616%. Why is that wrong?",
            "It is right",
            "²H is not 1.1%; ¹³C is 1.1% per carbon",
            "Oxygen causes M+1",
            "You should use n_C + n_O",
            "B",
            "Count carbons only for the 1.1% rule.",
        ),
        "D": fu(
            OC,
            "Student used n_C = 6 plus oxygens (n_C+n_O = 12) or 7.0×0.099.",
            "The 1.1% rule is per carbon atom. n_C + n_O = 12 would give 7.0×12×0.011 = 0.924, or other mixes near 0.693. Correct n?",
            "12",
            "8",
            "6",
            "16",
            "C",
            "Only the six carbons.",
        ),
    },
)


def _merge_astra(items: dict) -> None:
    """Fill gaps from Astra harness JSON. Authored records win."""
    from lbs_schema import validate_item

    astra_dir = Path(__file__).resolve().parents[1] / "out" / "astra"
    if not astra_dir.is_dir():
        return
    for p in sorted(astra_dir.glob("lbs_*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        uid = obj.get("uid")
        if not uid or uid in BANK:
            continue
        rec = {"solve": obj.get("solve"), "wrong": obj.get("wrong")}
        if validate_item(uid, rec, key=obj.get("key")):
            continue
        rec["source"] = "astra"
        items[uid] = rec


def build() -> dict:
    from lbs_gap import NEW

    items = dict(BANK)
    for uid, rec in NEW.items():
        items.setdefault(uid, rec)
    _merge_astra(items)
    items.setdefault("9701_w23_qp_13:q39", items["9701_w23_qp_11:q39"])
    items.setdefault("9701_w22_qp_13:q40", items.get("9701_w22_qp_11:q40"))
    items.setdefault("9701_w23_qp_13:q40", items.get("9701_w23_qp_11:q40"))
    items = {k: v for k, v in items.items() if v}
    doc = {
        "schema": "spectra.lbs.v2",
        "mx_types": [TS, CO, RR, SE, SF, MC, OC],
        "note": "Student runtime looks up followup by uid+wrong letter. mx_type is teacher-key only. Astra authors gaps offline.",
        "items": items,
        "n": len(items),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


if __name__ == "__main__":
    doc = build()
    missing_wrong = []
    for uid, rec in doc["items"].items():
        if len(rec["wrong"]) != 3:
            missing_wrong.append((uid, sorted(rec["wrong"])))
    print("wrote", OUT, "n", doc["n"], "incomplete", missing_wrong)
