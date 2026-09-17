"""Authored LBS for MCQs whose keys were recovered from mark schemes.

Used when Astra output is missing or fails schema. Same record shape as BANK.
"""
from __future__ import annotations

from lbs_followups import CO, MC, OC, RR, SE, SF, TS, fu, item

NEW = {}

NEW["9701_m18_qp_12:q30"] = item(
    "C₄H₁₀O isomers that absorb near 3400 cm⁻¹ (O–H) and 1200 cm⁻¹ (C–O) are the alcohols, not the ethers. There are four: butan-1-ol, butan-2-ol, 2-methylpropan-1-ol and 2-methylpropan-2-ol.",
    {
        "A": fu(
            SE,
            "Student counted only the straight-chain alcohols and under-extended the isomer count.",
            "How many alcohol isomers does C₄H₁₀O have?",
            "2 (butan-1-ol and butan-2-ol only)",
            "4 (those two plus the two methylpropanols)",
            "1",
            "8",
            "B",
            "Both branched C₄ alcohols also have O–H and C–O.",
        ),
        "C": fu(
            SE,
            "Student included ethers, which have C–O near 1200 cm⁻¹ but no O–H at 3400 cm⁻¹.",
            "An ether C₄H₁₀O shows C–O. Does it also show a strong broad band near 3400 cm⁻¹?",
            "Yes — all C₄H₁₀O isomers do",
            "No — 3400 cm⁻¹ is O–H; ethers have no O–H",
            "Yes — that band is C–H",
            "Only cyclic ethers do",
            "B",
            "The 3400 cm⁻¹ condition kills every ether. Do not count six.",
        ),
        "D": fu(
            OC,
            "Student over-counted by mixing alcohols, ethers and an extra invented isomer.",
            "C₄H₁₀O alcohol count that also matches 3400 + 1200 cm⁻¹ is four. What does 7 usually mean?",
            "The correct alcohol count",
            "Alcohols plus ethers plus at least one extra structure",
            "Only tertiary alcohols",
            "Only primary alcohols",
            "B",
            "Stay with the four alcohols.",
        ),
    },
)

NEW["9701_m19_qp_12:q30"] = item(
    "Broad ~3000 cm⁻¹ plus strong 1710 cm⁻¹ is carboxyl O–H + C=O: propanoic acid. An ester or ketone has C=O without that canyon; an alcohol has O–H higher up and no C=O.",
    {
        "A": fu(
            MC,
            "Student matches C=O to the ester and omits that esters have no broad 3000 cm⁻¹ O–H.",
            "Methyl propanoate has C=O. Does it show a very broad 2500–3000 cm⁻¹ O–H canyon?",
            "Yes",
            "No — esters have C=O + C–O and no O–H",
            "Yes, all carbonyl compounds do",
            "Only methyl esters do",
            "B",
            "The broad 3000 cm⁻¹ peak rules out the ester.",
        ),
        "B": fu(
            CO,
            "Student reads 3000 cm⁻¹ as alcohol O–H and omits the strong 1710 cm⁻¹ C=O.",
            "Propan-2-ol has alcohol O–H. Does it have a strong C=O at 1710 cm⁻¹?",
            "Yes",
            "No — alcohols have O–H and C–O, not C=O",
            "Yes, at 3400 cm⁻¹",
            "Yes, all C₃ compounds do",
            "B",
            "1710 cm⁻¹ is C=O. An alcohol cannot produce this pair.",
        ),
        "D": fu(
            CO,
            "Student matches 1710 cm⁻¹ to the ketone and omits the broad O–H.",
            "Propanone has a sharp C=O. What extra feature on this spectrum rules it out?",
            "Fingerprint peaks",
            "A broad absorption around 3000 cm⁻¹ (carboxyl O–H)",
            "C–H near 2900 cm⁻¹",
            "The absence of C≡N",
            "B",
            "A simple ketone has no O–H canyon.",
        ),
    },
)

NEW["9701_m20_qp_12:q23"] = item(
    "The plotted IR has a strong C=O near 1700 cm⁻¹ and no sharp C≡N near 2200–2250 cm⁻¹. C=O is present; C≡N is not.",
    {
        "A": fu(
            CO,
            "Student sees C=O and also awards C≡N without a 2200–2250 cm⁻¹ band.",
            "A nitrile C≡N, when present, is a sharp band in which range?",
            "1040–1300 cm⁻¹",
            "1640–1750 cm⁻¹",
            "2200–2250 cm⁻¹",
            "3200–3600 cm⁻¹",
            "C",
            "If that band is missing, C≡N is not present.",
        ),
        "B": fu(
            CO,
            "Student misses the carbonyl that is clearly on the plot.",
            "A strong sharp band near 1700 cm⁻¹ is which bond?",
            "C≡N",
            "C=O",
            "O–H",
            "C–O only",
            "B",
            "C=O is present, so ‘neither’ is false.",
        ),
        "D": fu(
            RR,
            "Student reverses the two assignments: calls the 1700 cm⁻¹ band C≡N.",
            "C≡N is 2200–2250 cm⁻¹; C=O is 1670–1750 cm⁻¹. A strong band near 1700 cm⁻¹ is?",
            "C≡N",
            "C=O",
            "O–H",
            "Neither",
            "B",
            "Do not swap the two ranges.",
        ),
    },
)

NEW["9701_s18_qp_13:q30"] = item(
    "S has no C=O (no strong 1670–1740 cm⁻¹). T has C=O at 1720 cm⁻¹ but no carboxyl canyon at 2500–3000 cm⁻¹, so T is a ketone (or aldehyde), not an acid. Only row B is an arene (no C=O) oxidised to a diketone (C=O, no O–H canyon). A and D make T an acid; C already puts a ketone on S.",
    {
        "A": fu(
            CO,
            "Student oxidises the terminal alkene to an acid and omits that T would then show the 2500–3000 cm⁻¹ canyon.",
            "T has 1720 cm⁻¹ but no strong broad 2500–3000 cm⁻¹ band. Can T be CH₃(CH₂)₅CO₂H?",
            "Yes — acids never show O–H",
            "No — a carboxylic acid must show that canyon",
            "Yes, if S is an alkene",
            "Yes, 1720 cm⁻¹ is O–H",
            "B",
            "The missing canyon kills every acid T.",
        ),
        "C": fu(
            CO,
            "Student keeps a structure for S that already contains CH₃CO– (a C=O), omitting S’s silent 1670–1740 cm⁻¹ region.",
            "S has no strong absorption between 1670 and 1740 cm⁻¹. Can S already contain a ketone C=O?",
            "Yes",
            "No — that band would be present",
            "Yes, ketones absorb only below 1000 cm⁻¹",
            "Yes, if T is also a ketone",
            "B",
            "C puts a carbonyl on S. It is out.",
        ),
        "D": fu(
            CO,
            "Student accepts an acid T (HO₂C–) despite the missing carboxyl canyon.",
            "A structure HO₂CCH₂CH₂COCH₂COCH₃ contains a carboxylic acid. Must it show 2500–3000 cm⁻¹ O–H?",
            "No",
            "Yes",
            "Only if there is no C=O",
            "Only in the fingerprint region",
            "B",
            "T’s missing canyon rules D out.",
        ),
    },
)

NEW["9701_s19_qp_13:q2"] = item(
    "Copper’s Aᵣ uses only the copper isotope peaks (63 and 65). The gold peak at 197 is a different element and must not enter the copper mean. Weight 63 and 65 by their abundances, then divide by the sum of those two abundances.",
    {
        "A": fu(
            OC,
            "Student put gold’s abundance into the denominator while omitting gold’s mass from the numerator.",
            "If you are finding Aᵣ of copper, which abundances belong in the denominator?",
            "Copper + gold",
            "Only the copper peak heights (63 and 65)",
            "Only gold",
            "The mass numbers 63 + 65",
            "B",
            "A mixes copper masses with a three-peak total. Inconsistent.",
        ),
        "B": fu(
            SE,
            "Student averaged copper and gold together as if they were isotopes of one element.",
            "Aᵣ of copper is the abundance-weighted mean of copper’s isotopes. Should m/e 197 (gold) enter that mean?",
            "Yes — every peak on the plot",
            "No — gold is a different element",
            "Yes, because it is an alloy",
            "Yes, Aᵣ is always the whole spectrum",
            "B",
            "An alloy’s spectrum contains more than one element. Use only Cu.",
        ),
        "D": fu(
            OC,
            "Student divided by the mass numbers instead of by the abundances.",
            "The weighted mean is Σ(m × abundance) / Σ(abundance). What is the correct denominator here?",
            "63 + 65",
            "56.36 + 25.14",
            "197",
            "100",
            "B",
            "Divide by the copper peak heights, not by the mass numbers.",
        ),
    },
)

NEW["9701_s22_qp_11:q40"] = item(
    "Functional groups in an organic compound are read from IR (characteristic absorptions). Mass spectrometry gives m/z of ions, not a functional-group table. Successive ionisation energies of sodium are not an IR or ordinary organic-MS experiment.",
    {
        "B": fu(
            MC,
            "Student conflates MS fragment peaks with IR functional-group identification.",
            "Which method is the syllabus tool for identifying organic functional groups from characteristic absorptions?",
            "Mass spectrometry",
            "Infrared spectroscopy",
            "A melting-point mixed test only",
            "Paper chromatography only",
            "B",
            "IR is the right choice for functional groups. Row A, not B.",
        ),
        "C": fu(
            MC,
            "Student assigns ionisation energies of Na to IR.",
            "Successive ionisation energies of sodium are energies to remove electrons from Na. Does infrared spectroscopy measure that?",
            "Yes — IR ionises atoms",
            "No — IR measures vibrational absorptions of bonds",
            "Yes, at 1710 cm⁻¹",
            "Yes, that is the fingerprint region",
            "B",
            "IR cannot give successive IE values of Na.",
        ),
        "D": fu(
            MC,
            "Student assigns successive IE of Na to a mass spectrum of the sort used for organic Mᵣ.",
            "A 9701 organic mass spectrum plots m/z of ions. Is that how successive ionisation energies of Na are obtained?",
            "Yes",
            "No — successive IE is a different experiment",
            "Yes, the M+1 peak is IE₂",
            "Yes, m/e 23 is IE₁",
            "B",
            "D uses the wrong method for the stated target.",
        ),
    },
)

NEW["9701_s22_qp_12:q40"] = item(
    "m/e 43 is C₃H₇⁺ or CH₃CO⁺. Ethanal gives CH₃CO⁺ (43). Propan-1-ol gives C₃H₇⁺ (43). Propan-2-ol also gives C₃H₇⁺ / CH₃CHCH₃-related 43. All three.",
    {
        "A": fu(
            SE,
            "Student keeps only the acylium ion from ethanal and under-extends 43 to the alcohols.",
            "Propan-1-ol can lose OH to give C₃H₇⁺. What is m/e of C₃H₇⁺?",
            "29",
            "31",
            "43",
            "60",
            "C",
            "Statement 2 is true as well. All three.",
        ),
        "B": fu(
            CO,
            "Student omits propan-2-ol’s C₃ fragment at 43.",
            "Propan-2-ol is C₃H₈O. Can it show a fragment at m/e 43 (C₃H₇⁺)?",
            "No, secondary alcohols never fragment",
            "Yes",
            "Only if a C=O is present",
            "Only in IR",
            "B",
            "Statement 3 is true. All three compounds.",
        ),
        "C": fu(
            CO,
            "Student drops ethanal, omitting CH₃CO⁺ = 43.",
            "Ethanal is CH₃CHO. The acylium ion CH₃CO⁺ has which m/e?",
            "15",
            "29",
            "43",
            "44",
            "C",
            "Statement 1 is true. All three.",
        ),
    },
)

NEW["9701_s23_qp_11:q40"] = item(
    "Bromine has two isotopes, so CHBr₃ has four molecular-ion peaks: all-light, one ⁸¹Br, two ⁸¹Br, three ⁸¹Br (M, M+2, M+4, M+6). Not 2, 3 or 6.",
    {
        "A": fu(
            OC,
            "Student counted the two bromine isotopes and stopped, as if the molecule were Br not CHBr₃.",
            "CHBr₃ contains three bromine atoms, each ⁷⁹Br or ⁸¹Br. How many different molecular-ion masses are there?",
            "2 (the two isotopes of Br)",
            "4 (0, 1, 2 or 3 of the heavier isotope)",
            "1",
            "3",
            "B",
            "Two isotopes of an atom ≠ two peaks for Br₃.",
        ),
        "B": fu(
            OC,
            "Student used a Br₂-style three-peak cluster (M, M+2, M+4) on a Br₃ molecule.",
            "Cl₂ or Br₂ shows three molecular-ion combinations. CHBr₃ has three bromines. Combinations of ⁷⁹Br/⁸¹Br?",
            "3",
            "4",
            "2",
            "9",
            "B",
            "k identical two-isotope atoms → k+1 molecular-ion peaks: 4.",
        ),
        "D": fu(
            OC,
            "Student counted 2³ = 8 and then trimmed, or counted every permutation as a separate m/e.",
            "⁷⁹Br₃, ⁷⁹Br₂⁸¹Br, ⁷⁹Br⁸¹Br₂ and ⁸¹Br₃ are four masses. Why is 6 too many?",
            "It counts permutations of the same isotope count as different m/e",
            "It is the right number",
            "Carbon has six isotopes",
            "Hydrogen has six isotopes",
            "A",
            "Mass cares how many ⁸¹Br atoms, not which position.",
        ),
    },
)

NEW["9701_w20_qp_12:q30"] = item(
    "The IR is an ester: strong C=O plus C–O, no alcohol O–H and no carboxyl canyon. Methyl ethanoate. A is a hydroxyketone (both C=O and O–H); B is an acid (canyon); D is an alkene (no C=O).",
    {
        "A": fu(
            CO,
            "Student matches C=O and omits that a hydroxyketone must also show alcohol O–H.",
            "CH₃COCH₂OH must show which pair?",
            "C=O only",
            "O–H only",
            "Both C=O near 1700 cm⁻¹ and alcohol O–H at 3200–3600 cm⁻¹",
            "C≡N",
            "C",
            "If the plot has no alcohol O–H, A is out.",
        ),
        "B": fu(
            CO,
            "Student matches C=O to the acid and omits the carboxyl canyon.",
            "CH₃CH₂CO₂H must show a very broad 2500–3000 cm⁻¹ O–H. If that canyon is absent, is the acid possible?",
            "Yes",
            "No",
            "Yes, acids have no O–H",
            "Yes, 1710 cm⁻¹ is O–H",
            "B",
            "No canyon, not the acid.",
        ),
        "D": fu(
            CO,
            "Student ignores the carbonyl that is on the plot.",
            "CH₃CH=CHCH₃ has C=C, not C=O. A strong ~1740 cm⁻¹ band is which bond?",
            "C=C",
            "C=O",
            "O–H",
            "C≡N",
            "B",
            "An alkene does not produce that C=O.",
        ),
    },
)

NEW["9701_w22_qp_11:q40"] = item(
    "M+1/M ≈ 1.1% × n_C. Ratio 13:1 means M+1/M = 1/13 ≈ 7.69%, so n_C ≈ 7.69/1.1 ≈ 7. 3,3-dimethylpentan-1-ol is C₇. Butyl butanoate is C₈, hexan-3-one C₆, 2,2,3-trimethylhexane C₉.",
    {
        "A": fu(
            OC,
            "Student used eight carbons (the ester C₈) instead of the 13:1 ratio.",
            "M+1/M = 1/13 ≈ 0.0769. n_C ≈ 0.0769 / 0.011. That is about how many carbons?",
            "8",
            "7",
            "13",
            "1",
            "B",
            "Butyl butanoate is C₈. The ratio is seven carbons.",
        ),
        "B": fu(
            OC,
            "Student picked a C₆ ketone.",
            "Hexan-3-one is C₆H₁₂O. Would M+1/M be about 6×1.1% = 6.6% (≈ 1:15), or 1:13?",
            "1:13",
            "Closer to 1:15 (six carbons)",
            "1:6",
            "1:1",
            "B",
            "Six carbons do not give 13:1.",
        ),
        "C": fu(
            OC,
            "Student picked a C₉ alkane.",
            "2,2,3-trimethylhexane is C₉H₂₀. 9×1.1% ≈ 9.9% is about 1:10, not 1:13. n_C for 1:13 is?",
            "9",
            "13",
            "7",
            "20",
            "C",
            "Count carbons from the ratio, then match the formula.",
        ),
    },
)

NEW["9701_w23_qp_11:q40"] = item(
    "M+1/M = 4/91 ≈ 0.044 → n_C ≈ 4.4/1.1 = 4. J is a C₄ molecule that oxidises with hot acidified dichromate to a carboxylic acid: butanal (aldehyde). Butanone (C₄ ketone) does not oxidise to an acid; propan-1-ol and propanenitrile are C₃.",
    {
        "B": fu(
            MC,
            "Student keeps four carbons but conflates ketone with aldehyde oxidation.",
            "Does butanone oxidise to a carboxylic acid with hot acidified K₂Cr₂O₇?",
            "Yes, all carbonyls do",
            "No — ketones are not oxidised under these conditions",
            "Yes, to butanal first",
            "Yes, to propanoic acid",
            "B",
            "J must be oxidisable to an acid: the aldehyde, not the ketone.",
        ),
        "C": fu(
            OC,
            "Student picked a primary alcohol that would become an acid but is C₃, not C₄.",
            "M+1/M = 4/91 gives n_C ≈ 4. Propan-1-ol is C₃H₈O. Can it be J?",
            "Yes, alcohols always match 4:91",
            "No — it has three carbons",
            "Yes, because it oxidises to an acid",
            "Yes, n_C is the number of oxygens",
            "B",
            "Right chemistry, wrong carbon count.",
        ),
        "D": fu(
            OC,
            "Student picked a C₃ nitrile that also does not oxidise to an acid under these conditions.",
            "Propanenitrile is C₃H₅N. Does 4:91 match three carbons, and does hot dichromate turn a nitrile into a carboxylic acid in this question’s sense?",
            "Yes and yes",
            "No — n_C is 3, and the intended oxidisable group is aldehyde (or 1° alcohol)",
            "Yes, nitriles always give 4:91",
            "Yes, 91 is nitrogen",
            "B",
            "Four carbons + oxidisable to acid → butanal.",
        ),
    },
)

# clones
NEW["9701_w22_qp_13:q40"] = NEW["9701_w22_qp_11:q40"]
NEW["9701_w23_qp_13:q40"] = NEW["9701_w23_qp_11:q40"]
# same polyol IR as w23_qp_11:q39 / w18_qp_12:q30 — filled in lbs_followups.build
