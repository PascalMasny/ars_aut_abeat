# Catalog Manifest

Generated 2026-07-20T10:47:35Z — the exact source set the installation was built from.

The generated picture sequences are **deterministic**: `iterate_degrade.py` seeds each
artwork with `zlib.crc32(stem)` and each chained step with `seed + i`. Re-downloading the
same Met object IDs under the same filenames and re-running the pipeline with unchanged
`DIRECT_*`/`CHAIN_*`/`GUIDANCE`/`STEPS` reproduces byte-identical pictures — except for the
LLaVA prompt, which is not deterministic (see `docs/HOWTO_REGENERATE_CATALOG.md`).

## Summary

| Set | Count | Size | Status |
|-----|-------|------|--------|
| `catalog/` source JPEGs | 169 | 362 MB | deleted — re-downloadable |
| `catalog_iterations_10/` (11 pictures each) | 169 dirs / 1,859 files | 11 GB | deleted — regenerable |
| `catalog_iterations/` (101 frames each, legacy) | 120 dirs / ~12,120 files | 98 GB | deleted — superseded, do not regenerate |
| `_archive/` | — | 1.6 GB | deleted — superseded |

## Source artworks (169)

Filename stem = artwork slug = DB `slug` = SD seed input. Trailing number is the Met object ID.

| # | Slug | Met object ID |
|---|------|---------------|
| 1 | `A_Donor_Presented_by_a_Saint_436284` | [436284](https://www.metmuseum.org/art/collection/search/436284) |
| 2 | `A_Woman_Reading_435991` | [435991](https://www.metmuseum.org/art/collection/search/435991) |
| 3 | `A_Young_Woman_as_a_Shepherdess_437405` | [437405](https://www.metmuseum.org/art/collection/search/437405) |
| 4 | `Allegory_of_the_Arts_437946` | [437946](https://www.metmuseum.org/art/collection/search/437946) |
| 5 | `An_Egyptian_Peasant_Woman_and_Her_Child_435711` | [435711](https://www.metmuseum.org/art/collection/search/435711) |
| 6 | `Antoine_Dominique_Sauveur_Aubert_born_1817_the_Art_435870` | [435870](https://www.metmuseum.org/art/collection/search/435870) |
| 7 | `Benedikt_von_Hertenstein_born_about_1495_died_1522_436657` | [436657](https://www.metmuseum.org/art/collection/search/436657) |
| 8 | `Bronze_mirror_247874` | [247874](https://www.metmuseum.org/art/collection/search/247874) |
| 9 | `Bronze_oinochoe_256864` | [256864](https://www.metmuseum.org/art/collection/search/256864) |
| 10 | `Bronze_oinochoe_jug_and_handle_attachment_254510` | [254510](https://www.metmuseum.org/art/collection/search/254510) |
| 11 | `Bronze_statuette_of_a_solar_deity_249096` | [249096](https://www.metmuseum.org/art/collection/search/249096) |
| 12 | `Bronze_statuette_of_Hercules_256650` | [256650](https://www.metmuseum.org/art/collection/search/256650) |
| 13 | `Bronze_strainer_with_openwork_handle_248652` | [248652](https://www.metmuseum.org/art/collection/search/248652) |
| 14 | `Bronze_thymiaterion_incense_burner_256135` | [256135](https://www.metmuseum.org/art/collection/search/256135) |
| 15 | `Bronze_thymiaterion_incense_burner_with_Marsyas_255400` | [255400](https://www.metmuseum.org/art/collection/search/255400) |
| 16 | `Bronze_torso_of_a_youth_250947` | [250947](https://www.metmuseum.org/art/collection/search/250947) |
| 17 | `Brother_Gregorio_Belo_of_Vicenza_436917` | [436917](https://www.metmuseum.org/art/collection/search/436917) |
| 18 | `Carlo_Rimbotti_15181591_761570` | [761570](https://www.metmuseum.org/art/collection/search/761570) |
| 19 | `Christ_Bearing_the_Cross_437202` | [437202](https://www.metmuseum.org/art/collection/search/437202) |
| 20 | `Christ_Blessing_439327` | [439327](https://www.metmuseum.org/art/collection/search/439327) |
| 21 | `Circus_Sideshow_Parade_de_cirque_437654` | [437654](https://www.metmuseum.org/art/collection/search/437654) |
| 22 | `Colossal_marble_head_of_the_emperor_Augustus_251114` | [251114](https://www.metmuseum.org/art/collection/search/251114) |
| 23 | `Cypresses_437980` | [437980](https://www.metmuseum.org/art/collection/search/437980) |
| 24 | `Diana_and_Cupid_435622` | [435622](https://www.metmuseum.org/art/collection/search/435622) |
| 25 | `Diana_the_Huntress_436499` | [436499](https://www.metmuseum.org/art/collection/search/436499) |
| 26 | `Don_Andrés_de_Andrade_y_la_Cal_437173` | [437173](https://www.metmuseum.org/art/collection/search/437173) |
| 27 | `Flora_and_Zephyr_435573` | [435573](https://www.metmuseum.org/art/collection/search/435573) |
| 28 | `Fragment_of_a_terracotta_neck-amphora_jar_256335` | [256335](https://www.metmuseum.org/art/collection/search/256335) |
| 29 | `Fragmentary_marble_head_of_a_girl_248586` | [248586](https://www.metmuseum.org/art/collection/search/248586) |
| 30 | `Fragments_of_a_marble_statue_of_the_Diadoumenos_yo_251838` | [251838](https://www.metmuseum.org/art/collection/search/251838) |
| 31 | `Gilt_bronze_ring_253709` | [253709](https://www.metmuseum.org/art/collection/search/253709) |
| 32 | `Gustave_Boyer_b_1840_in_a_Straw_Hat_435873` | [435873](https://www.metmuseum.org/art/collection/search/435873) |
| 33 | `Head_of_Christ_Ecce_Homo_435897` | [435897](https://www.metmuseum.org/art/collection/search/435897) |
| 34 | `Ia_Orana_Maria_Hail_Mary_438821` | [438821](https://www.metmuseum.org/art/collection/search/438821) |
| 35 | `Inscribed_marble_base_241986` | [241986](https://www.metmuseum.org/art/collection/search/241986) |
| 36 | `Jacob_Willemsz_van_Veen_14561535_the_Artists_Fathe_436638` | [436638](https://www.metmuseum.org/art/collection/search/436638) |
| 37 | `Jacques-Louis_Leblanc_17741846_436706` | [436706](https://www.metmuseum.org/art/collection/search/436706) |
| 38 | `James_Stuart_16121655_Duke_of_Richmond_and_Lennox_436252` | [436252](https://www.metmuseum.org/art/collection/search/436252) |
| 39 | `Jasper_intaglio_Sol_in_a_quadriga_four-horse_chari_245140` | [245140](https://www.metmuseum.org/art/collection/search/245140) |
| 40 | `Jupiter_in_the_Guise_of_Diana_and_Callisto_435747` | [435747](https://www.metmuseum.org/art/collection/search/435747) |
| 41 | `Leda_and_the_Swan_435594` | [435594](https://www.metmuseum.org/art/collection/search/435594) |
| 42 | `Limestone_Geryon_242142` | [242142](https://www.metmuseum.org/art/collection/search/242142) |
| 43 | `Madame_Bergeret_de_Frouville_as_Diana_437183` | [437183](https://www.metmuseum.org/art/collection/search/437183) |
| 44 | `Madame_Cézanne_Hortense_Fiquet_18501922_in_a_Red_D_435876` | [435876](https://www.metmuseum.org/art/collection/search/435876) |
| 45 | `Madame_Georges_Charpentier_Marguerite-Louise_Lemon_438815` | [438815](https://www.metmuseum.org/art/collection/search/438815) |
| 46 | `Madame_Jacques-Louis_Leblanc_Françoise_Poncelle_17_436703` | [436703](https://www.metmuseum.org/art/collection/search/436703) |
| 47 | `Madonna_Adoring_the_Sleeping_Child_435640` | [435640](https://www.metmuseum.org/art/collection/search/435640) |
| 48 | `Madonna_and_Child_438754` | [438754](https://www.metmuseum.org/art/collection/search/438754) |
| 49 | `Man_in_Prayer_435837` | [435837](https://www.metmuseum.org/art/collection/search/435837) |
| 50 | `Marble_and_bronze_table_247464` | [247464](https://www.metmuseum.org/art/collection/search/247464) |
| 51 | `Marble_female_figure_255595` | [255595](https://www.metmuseum.org/art/collection/search/255595) |
| 52 | `Marble_funerary_altar_257855` | [257855](https://www.metmuseum.org/art/collection/search/257855) |
| 53 | `Marble_funerary_statues_of_a_maiden_and_a_little_g_254508` | [254508](https://www.metmuseum.org/art/collection/search/254508) |
| 54 | `Marble_grave_relief_with_two_portrait_busts_248139` | [248139](https://www.metmuseum.org/art/collection/search/248139) |
| 55 | `Marble_grave_stele_of_a_young_woman_and_servant_253505` | [253505](https://www.metmuseum.org/art/collection/search/253505) |
| 56 | `Marble_head_of_a_bearded_man_248112` | [248112](https://www.metmuseum.org/art/collection/search/248112) |
| 57 | `Marble_head_of_a_boy_wearing_a_wreath_248880` | [248880](https://www.metmuseum.org/art/collection/search/248880) |
| 58 | `Marble_head_of_a_child_255424` | [255424](https://www.metmuseum.org/art/collection/search/255424) |
| 59 | `Marble_head_of_a_goddess_248268` | [248268](https://www.metmuseum.org/art/collection/search/248268) |
| 60 | `Marble_head_of_a_Hellenistic_ruler_246992` | [246992](https://www.metmuseum.org/art/collection/search/246992) |
| 61 | `Marble_head_of_a_woman_wearing_a_diadem_251349` | [251349](https://www.metmuseum.org/art/collection/search/251349) |
| 62 | `Marble_head_of_a_young_woman_252504` | [252504](https://www.metmuseum.org/art/collection/search/252504) |
| 63 | `Marble_herm_head_of_a_bearded_deity_256121` | [256121](https://www.metmuseum.org/art/collection/search/256121) |
| 64 | `Marble_inscription_fragment_241931` | [241931](https://www.metmuseum.org/art/collection/search/241931) |
| 65 | `Marble_Kore_statuette_247988` | [247988](https://www.metmuseum.org/art/collection/search/247988) |
| 66 | `Marble_portrait_bust_of_a_man_248118` | [248118](https://www.metmuseum.org/art/collection/search/248118) |
| 67 | `Marble_portrait_bust_of_a_man_248467` | [248467](https://www.metmuseum.org/art/collection/search/248467) |
| 68 | `Marble_portrait_head_of_a_man_248314` | [248314](https://www.metmuseum.org/art/collection/search/248314) |
| 69 | `Marble_portrait_head_of_a_woman_259248` | [259248](https://www.metmuseum.org/art/collection/search/259248) |
| 70 | `Marble_portrait_of__Matidia_Minor_251061` | [251061](https://www.metmuseum.org/art/collection/search/251061) |
| 71 | `Marble_portrait_of_a_man_247990` | [247990](https://www.metmuseum.org/art/collection/search/247990) |
| 72 | `Marble_portrait_of_the_emperor_Augustus_248119` | [248119](https://www.metmuseum.org/art/collection/search/248119) |
| 73 | `Marble_sarcophagus_lid_with_reclining_couple_256163` | [256163](https://www.metmuseum.org/art/collection/search/256163) |
| 74 | `Marble_sarcophagus_with_flying_erotes_holding_a_cl_254855` | [254855](https://www.metmuseum.org/art/collection/search/254855) |
| 75 | `Marble_spouted_bowl_256286` | [256286](https://www.metmuseum.org/art/collection/search/256286) |
| 76 | `Marble_statue_of_a_girl_246993` | [246993](https://www.metmuseum.org/art/collection/search/246993) |
| 77 | `Marble_statue_of_a_kouros_youth_253370` | [253370](https://www.metmuseum.org/art/collection/search/253370) |
| 78 | `Marble_statue_of_a_lion_248140` | [248140](https://www.metmuseum.org/art/collection/search/248140) |
| 79 | `Marble_statue_of_an_old_fisherman_250748` | [250748](https://www.metmuseum.org/art/collection/search/250748) |
| 80 | `Marble_statue_of_an_old_woman_248132` | [248132](https://www.metmuseum.org/art/collection/search/248132) |
| 81 | `Marble_statue_of_Aphrodite_251115` | [251115](https://www.metmuseum.org/art/collection/search/251115) |
| 82 | `Marble_statue_of_Aphrodite_254697` | [254697](https://www.metmuseum.org/art/collection/search/254697) |
| 83 | `Marble_statue_of_the_Diadoumenos_youth_tying_a_fil_246991` | [246991](https://www.metmuseum.org/art/collection/search/246991) |
| 84 | `Marble_statue_of_Tyche-Fortuna_restored_with_the_p_255111` | [255111](https://www.metmuseum.org/art/collection/search/255111) |
| 85 | `Marble_statuette_of_a_satyr_248702` | [248702](https://www.metmuseum.org/art/collection/search/248702) |
| 86 | `Marble_statuette_of_Aphrodite_251844` | [251844](https://www.metmuseum.org/art/collection/search/251844) |
| 87 | `Marble_torso_of_a_boy_248798` | [248798](https://www.metmuseum.org/art/collection/search/248798) |
| 88 | `Medea_Rejuvenating_Aeson_441234` | [441234](https://www.metmuseum.org/art/collection/search/441234) |
| 89 | `Merrymakers_at_Shrovetide_436622` | [436622](https://www.metmuseum.org/art/collection/search/436622) |
| 90 | `Moses_and_Aaron_before_Pharaoh_An_Allegory_of_the__437217` | [437217](https://www.metmuseum.org/art/collection/search/437217) |
| 91 | `Neck-amphora_256609` | [256609](https://www.metmuseum.org/art/collection/search/256609) |
| 92 | `Portrait_of_a_Man_437875` | [437875](https://www.metmuseum.org/art/collection/search/437875) |
| 93 | `Portrait_of_a_Man_in_a_Chaperon_437488` | [437488](https://www.metmuseum.org/art/collection/search/437488) |
| 94 | `Portrait_of_a_Woman_in_Gray_436152` | [436152](https://www.metmuseum.org/art/collection/search/436152) |
| 95 | `Portrait_of_a_Young_Man_436409` | [436409](https://www.metmuseum.org/art/collection/search/436409) |
| 96 | `Portrait_of_a_Young_Woman_437205` | [437205](https://www.metmuseum.org/art/collection/search/437205) |
| 97 | `Saint_Paul_with_a_Donor_Christ_Appearing_to_His_Mo_437032` | [437032](https://www.metmuseum.org/art/collection/search/437032) |
| 98 | `Seated_Peasant_437990` | [437990](https://www.metmuseum.org/art/collection/search/437990) |
| 99 | `Sebastián_Martínez_y_Pérez_17471800_436541` | [436541](https://www.metmuseum.org/art/collection/search/436541) |
| 100 | `Sketch_for_Reception_of_Emperor_Napoleon_III_and_E_441374` | [441374](https://www.metmuseum.org/art/collection/search/441374) |
| 101 | `Statue_of_Dionysos_leaning_on_a_female_f_255973` | [255973](https://www.metmuseum.org/art/collection/search/255973) |
| 102 | `Statuette_of_a_Youth_246281` | [246281](https://www.metmuseum.org/art/collection/search/246281) |
| 103 | `Statuette_of_female_figure_246306` | [246306](https://www.metmuseum.org/art/collection/search/246306) |
| 104 | `Steatite_bust_252450` | [252450](https://www.metmuseum.org/art/collection/search/252450) |
| 105 | `Still_Life_with_Apples_and_a_Pot_of_Primroses_435882` | [435882](https://www.metmuseum.org/art/collection/search/435882) |
| 106 | `Still_Life_with_Pansies_436294` | [436294](https://www.metmuseum.org/art/collection/search/436294) |
| 107 | `Study_of_a_Female_Nude_438661` | [438661](https://www.metmuseum.org/art/collection/search/438661) |
| 108 | `Terracotta_amphora_jar_255154` | [255154](https://www.metmuseum.org/art/collection/search/255154) |
| 109 | `Terracotta_bobbin_252976` | [252976](https://www.metmuseum.org/art/collection/search/252976) |
| 110 | `Terracotta_calyx-krater_bowl_for_mixing_wine_and_w_254930` | [254930](https://www.metmuseum.org/art/collection/search/254930) |
| 111 | `Terracotta_column-krater_bowl_for_mixing_wine_and__253349` | [253349](https://www.metmuseum.org/art/collection/search/253349) |
| 112 | `Terracotta_figure_of_a_woman_247569` | [247569](https://www.metmuseum.org/art/collection/search/247569) |
| 113 | `Terracotta_fragment_of_a_calyx-krater_bowl_for_mix_733175` | [733175](https://www.metmuseum.org/art/collection/search/733175) |
| 114 | `Terracotta_fragment_of_a_kylix_drinking_cup_699232` | [699232](https://www.metmuseum.org/art/collection/search/699232) |
| 115 | `Terracotta_fragment_of_a_stamnos_jar_750012` | [750012](https://www.metmuseum.org/art/collection/search/750012) |
| 116 | `Terracotta_fragment_of_a_volute-krater_bowl_for_mi_728785` | [728785](https://www.metmuseum.org/art/collection/search/728785) |
| 117 | `Terracotta_funerary_plaque_248909` | [248909](https://www.metmuseum.org/art/collection/search/248909) |
| 118 | `Terracotta_head_of_a_deer_248411` | [248411](https://www.metmuseum.org/art/collection/search/248411) |
| 119 | `Terracotta_kylix_eye-cup_drinking_cup_248906` | [248906](https://www.metmuseum.org/art/collection/search/248906) |
| 120 | `Terracotta_lekythos_oil_flask_247386` | [247386](https://www.metmuseum.org/art/collection/search/247386) |
| 121 | `Terracotta_lekythos_oil_flask_248100` | [248100](https://www.metmuseum.org/art/collection/search/248100) |
| 122 | `Terracotta_Little_Master_cup_247100` | [247100](https://www.metmuseum.org/art/collection/search/247100) |
| 123 | `Terracotta_oinochoe_jug_247372` | [247372](https://www.metmuseum.org/art/collection/search/247372) |
| 124 | `Terracotta_oinochoe_jug_247374` | [247374](https://www.metmuseum.org/art/collection/search/247374) |
| 125 | `Terracotta_pyxis_box_247286` | [247286](https://www.metmuseum.org/art/collection/search/247286) |
| 126 | `Terracotta_rim_fragment_of_a_kylix_drinking_cup_756271` | [756271](https://www.metmuseum.org/art/collection/search/756271) |
| 127 | `Terracotta_skyphos_deep_drinking_cup_253031` | [253031](https://www.metmuseum.org/art/collection/search/253031) |
| 128 | `Terracotta_stand_253342` | [253342](https://www.metmuseum.org/art/collection/search/253342) |
| 129 | `Terracotta_vase_with_relief_decoration_246674` | [246674](https://www.metmuseum.org/art/collection/search/246674) |
| 130 | `Terracotta_vase_with_relief_decoration_246675` | [246675](https://www.metmuseum.org/art/collection/search/246675) |
| 131 | `Terracotta_volute-krater_bowl_for_mixing_wine_and__247964` | [247964](https://www.metmuseum.org/art/collection/search/247964) |
| 132 | `The_Adoration_of_the_Magi_436803` | [436803](https://www.metmuseum.org/art/collection/search/436803) |
| 133 | `The_Adoration_of_the_Magi_436984` | [436984](https://www.metmuseum.org/art/collection/search/436984) |
| 134 | `The_Adoration_of_the_Shepherds_436966` | [436966](https://www.metmuseum.org/art/collection/search/436966) |
| 135 | `The_Birth_and_Naming_of_Saint_John_the_Baptist_rev_438467` | [438467](https://www.metmuseum.org/art/collection/search/438467) |
| 136 | `The_Birth_of_the_Virgin_435848` | [435848](https://www.metmuseum.org/art/collection/search/435848) |
| 137 | `The_Card_Players_435868` | [435868](https://www.metmuseum.org/art/collection/search/435868) |
| 138 | `The_Cellier_Altarpiece_435638` | [435638](https://www.metmuseum.org/art/collection/search/435638) |
| 139 | `The_Chariot_of_Aurora_438026` | [438026](https://www.metmuseum.org/art/collection/search/438026) |
| 140 | `The_Crucifixion_The_Last_Judgment_436282` | [436282](https://www.metmuseum.org/art/collection/search/436282) |
| 141 | `The_Dance_Class_438817` | [438817](https://www.metmuseum.org/art/collection/search/438817) |
| 142 | `The_Fifteen_Mysteries_and_the_Virgin_of_the_Rosary_437216` | [437216](https://www.metmuseum.org/art/collection/search/437216) |
| 143 | `The_Forest_in_Winter_at_Sunset_438816` | [438816](https://www.metmuseum.org/art/collection/search/438816) |
| 144 | `The_French_Comedians_437925` | [437925](https://www.metmuseum.org/art/collection/search/437925) |
| 145 | `The_Garter_438126` | [438126](https://www.metmuseum.org/art/collection/search/438126) |
| 146 | `The_Hall_of_Antiquities_at_Charlottenborg_Palace_C_780292` | [780292](https://www.metmuseum.org/art/collection/search/780292) |
| 147 | `The_Harvesters_435809` | [435809](https://www.metmuseum.org/art/collection/search/435809) |
| 148 | `The_Holy_Family_436793` | [436793](https://www.metmuseum.org/art/collection/search/436793) |
| 149 | `The_Horse_Fair_435702` | [435702](https://www.metmuseum.org/art/collection/search/435702) |
| 150 | `The_Last_Communion_of_Saint_Jerome_435728` | [435728](https://www.metmuseum.org/art/collection/search/435728) |
| 151 | `The_Martyrdom_of_Saint_John_the_Baptist_440209` | [440209](https://www.metmuseum.org/art/collection/search/440209) |
| 152 | `The_Monet_Family_in_Their_Garden_at_Argenteuil_436965` | [436965](https://www.metmuseum.org/art/collection/search/436965) |
| 153 | `The_Rest_on_the_Flight_into_Egypt_436987` | [436987](https://www.metmuseum.org/art/collection/search/436987) |
| 154 | `The_Resurrection_436416` | [436416](https://www.metmuseum.org/art/collection/search/436416) |
| 155 | `The_Toilette_of_Venus_435739` | [435739](https://www.metmuseum.org/art/collection/search/435739) |
| 156 | `The_Triumph_of_Fame_reverse_Impresa_of_the_Medici__436516` | [436516](https://www.metmuseum.org/art/collection/search/436516) |
| 157 | `Tommaso_di_Folco_Portinari_14281501_Maria_Portinar_437056` | [437056](https://www.metmuseum.org/art/collection/search/437056) |
| 158 | `Top_of_a_marble_funerary_relief_with_portrait_bust_250707` | [250707](https://www.metmuseum.org/art/collection/search/250707) |
| 159 | `Two_marble_portrait_heads_from_a_relief_250680` | [250680](https://www.metmuseum.org/art/collection/search/250680) |
| 160 | `Two_Tahitian_Women_436446` | [436446](https://www.metmuseum.org/art/collection/search/436446) |
| 161 | `Vase_fragment_250359` | [250359](https://www.metmuseum.org/art/collection/search/250359) |
| 162 | `Virgin_and_Child_435762` | [435762](https://www.metmuseum.org/art/collection/search/435762) |
| 163 | `Virgin_and_Child_436795` | [436795](https://www.metmuseum.org/art/collection/search/436795) |
| 164 | `Virgin_and_Child_437033` | [437033](https://www.metmuseum.org/art/collection/search/437033) |
| 165 | `Virgin_and_Child_437062` | [437062](https://www.metmuseum.org/art/collection/search/437062) |
| 166 | `Virgin_and_Child_in_a_Niche_436283` | [436283](https://www.metmuseum.org/art/collection/search/436283) |
| 167 | `Woman_in_a_Riding_Habit_LAmazone_436024` | [436024](https://www.metmuseum.org/art/collection/search/436024) |
| 168 | `Young_Man_and_Woman_in_an_Inn_436616` | [436616](https://www.metmuseum.org/art/collection/search/436616) |
| 169 | `Young_Man_Holding_a_Book_437030` | [437030](https://www.metmuseum.org/art/collection/search/437030) |
