# Yoga library: expert review list (gate M4)

100 yogas and doshas. For each one, please check three things:

1. The condition matches the classical definition.
2. The source is right.
3. The English, Hindi and Marathi texts read well.

When a rule is approved, set `reviewed: true` in its YAML file under `packages/engine/src/jyotish_engine/rules/`.
The conditions are simplified where the classics add strength tests. Those cases are marked *simplified* below.

## Original 26 (first release)

| # | Yoga | What the app checks | Source | Kind |
|---|---|---|---|---|
| 1 | Ruchaka Yoga<br>रुचक योग | Mars is strong in a kendra. | Phaladeepika ch. 6 (Pancha Mahapurusha) | yoga |
| 2 | Bhadra Yoga<br>भद्र योग | Mercury is strong in a kendra. | Phaladeepika ch. 6 (Pancha Mahapurusha) | yoga |
| 3 | Hamsa Yoga<br>हंस योग | Jupiter is strong in a kendra. | Phaladeepika ch. 6 (Pancha Mahapurusha) | yoga |
| 4 | Malavya Yoga<br>मालव्य योग | Venus is strong in a kendra. | Phaladeepika ch. 6 (Pancha Mahapurusha) | yoga |
| 5 | Sasa Yoga<br>शश योग | Saturn is strong in a kendra. | Phaladeepika ch. 6 (Pancha Mahapurusha) | yoga |
| 6 | Gaja Kesari Yoga<br>गजकेसरी योग | Jupiter is in a kendra from the Moon. | Phaladeepika ch. 6 | yoga |
| 7 | Sunapha Yoga<br>सुनफा योग | A planet occupies the 2nd house from the Moon. | Phaladeepika ch. 6 (Chandra yogas) | yoga |
| 8 | Anapha Yoga<br>अनफा योग | A planet occupies the 12th house from the Moon. | Phaladeepika ch. 6 (Chandra yogas) | yoga |
| 9 | Durudhara Yoga<br>दुरुधरा योग | Planets occupy both the 2nd and 12th houses from the Moon. | Phaladeepika ch. 6 (Chandra yogas) | yoga |
| 10 | Kemadruma Yoga<br>केमद्रुम योग | No planet supports the Moon from the 2nd or 12th house and none is in a kendra from the Lagna. | Phaladeepika ch. 6 (Chandra yogas) | dosha |
| 11 | Vesi Yoga<br>वेशि योग | A planet occupies the 2nd house from the Sun. | Phaladeepika ch. 6 (Surya yogas) | yoga |
| 12 | Vasi Yoga<br>वाशि योग | A planet occupies the 12th house from the Sun. | Phaladeepika ch. 6 (Surya yogas) | yoga |
| 13 | Ubhayachari Yoga<br>उभयचरी योग | Planets occupy both the 2nd and 12th houses from the Sun. | Phaladeepika ch. 6 (Surya yogas) | yoga |
| 14 | Budha-Aditya Yoga<br>बुधादित्य योग | The Sun and Mercury are together and Mercury is not combust. | Common tradition (Sun-Mercury conjunction) | yoga |
| 15 | Chandra-Mangala Yoga<br>चंद्र-मंगल योग | The Moon and Mars are together. | Phaladeepika ch. 6 | yoga |
| 16 | Adhi Yoga<br>अधि योग | Mercury, Jupiter and Venus are in the 6th, 7th or 8th from the Moon. | Phaladeepika ch. 6 | yoga |
| 17 | Amala Yoga<br>अमला योग | A natural benefic is in the 10th house from the Lagna or the Moon. | Phaladeepika ch. 6 | yoga |
| 18 | Raja Yoga<br>राज योग | The lord of a kendra and the lord of a trikona are together. | BPHS, Raja yoga chapter (kendra and trikona lords together) | yoga |
| 19 | Dhana Yoga<br>धन योग | A wealth lord (2nd or 11th) is together with a fortune lord (5th or 9th). | BPHS, Dhana yoga chapter (lords of 2/11 with lords of 5/9) | yoga |
| 20 | Harsha Yoga (Viparita Raja)<br>हर्ष योग (विपरीत राज योग) | The 6th lord sits in a dusthana. | Uttara Kalamrita (Viparita Raja yogas) | yoga |
| 21 | Sarala Yoga (Viparita Raja)<br>सरल योग (विपरीत राज योग) | The 8th lord sits in a dusthana. | Uttara Kalamrita (Viparita Raja yogas) | yoga |
| 22 | Vimala Yoga (Viparita Raja)<br>विमल योग (विपरीत राज योग) | The 12th lord sits in a dusthana. | Uttara Kalamrita (Viparita Raja yogas) | yoga |
| 23 | Neecha Bhanga<br>नीच भंग | A debilitated planet has its weakness cancelled because its sign lord, or the planet exalted there, is in a kendra. | Phaladeepika ch. 7 (Neecha Bhanga) | yoga |
| 24 | Shakata Yoga<br>शकट योग | The Moon is in the 6th, 8th or 12th from Jupiter. | Phaladeepika ch. 6 | dosha |
| 25 | Manglik (Kuja dosha)<br>मांगलिक (कुज दोष) | Mars is in the 1st, 2nd, 4th, 7th, 8th or 12th from the Lagna or the Moon. Many traditions check this in marriage matching; there are several cancelling conditions, so an astrologer should look at the full picture. | Common tradition (Kuja dosha: Mars in 1, 2, 4, 7, 8, 12) | dosha |
| 26 | Kala Sarpa<br>काल सर्प | All seven planets lie on one side of the Rahu-Ketu axis. This is a later tradition and is not described in BPHS; read it with care. | Later tradition (not in BPHS): all planets on one side of the Rahu-Ketu axis | dosha |

## Nabhasa yogas (new)

| # | Yoga | What the app checks | Source | Kind |
|---|---|---|---|---|
| 1 | Rajju Yoga<br>रज्जु योग | All seven planets are in movable signs. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 2 | Musala Yoga<br>मुसल योग | All seven planets are in fixed signs. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 3 | Nala Yoga<br>नल योग | All seven planets are in dual signs. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 4 | Mala Yoga *(simplified)*<br>माला योग | Benefics (Moon, Mercury, Jupiter, Venus) occupy three of the four kendras. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 5 | Sarpa Yoga *(simplified)*<br>सर्प योग | Malefics (Sun, Mars, Saturn) occupy three of the four kendras. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 6 | Gada Yoga<br>गदा योग | All planets sit in two neighbouring kendras. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 7 | Shakata Yoga (Nabhasa)<br>शकट योग (नाभस) | All planets are in the 1st and 7th houses. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 8 | Vihaga Yoga<br>विहग योग | All planets are in the 4th and 10th houses. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 9 | Sringataka Yoga<br>शृंगाटक योग | All planets are in the trikonas (1st, 5th and 9th). | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 10 | Hala Yoga<br>हल योग | All planets are in mutual trines other than those of the Lagna. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 11 | Vajra Yoga *(simplified)*<br>वज्र योग | Mercury, Jupiter and Venus are in the 1st and 7th, and the Sun, Mars and Saturn in the 4th and 10th. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 12 | Yava Yoga *(simplified)*<br>यव योग | The Sun, Mars and Saturn are in the 1st and 7th, and Mercury, Jupiter and Venus in the 4th and 10th. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 13 | Kamala Yoga<br>कमल योग | All planets are in the four kendras, with each kendra occupied. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 14 | Vapi Yoga<br>वापी योग | All planets avoid the kendras and sit in the succeedent or cadent houses. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 15 | Yupa Yoga<br>यूप योग | All planets fill the four houses from the 1st to the 4th. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 16 | Shara Yoga<br>शर योग | All planets fill the four houses from the 4th to the 7th. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 17 | Shakti Yoga<br>शक्ति योग | All planets fill the four houses from the 7th to the 10th. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 18 | Danda Yoga<br>दंड योग | All planets fill the four houses from the 10th to the 1st. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 19 | Nauka Yoga<br>नौका योग | All planets fill seven houses in a row from the 1st. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 20 | Koota Yoga<br>कूट योग | All planets fill seven houses in a row from the 4th. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 21 | Chhatra Yoga<br>छत्र योग | All planets fill seven houses in a row from the 7th. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 22 | Chapa Yoga<br>चाप योग | All planets fill seven houses in a row from the 10th. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 23 | Ardhachandra Yoga<br>अर्धचंद्र योग | All planets fill seven houses in a row that starts away from a kendra. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 24 | Chakra Yoga<br>चक्र योग | All planets are in the six odd houses from the Lagna, each occupied. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 25 | Samudra Yoga<br>समुद्र योग | All planets are in the six even houses from the Lagna, each occupied. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 26 | Vallaki (Veena) Yoga<br>वल्लकी (वीणा) योग | The planets occupy seven different signs. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 27 | Damini Yoga<br>दामिनी योग | The planets occupy six signs. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 28 | Pasa Yoga<br>पाश योग | The planets occupy five signs. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 29 | Kedara Yoga<br>केदार योग | The planets occupy four signs. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 30 | Shula Yoga<br>शूल योग | The planets occupy only three signs. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 31 | Yuga Yoga<br>युग योग | The planets occupy only two signs. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |
| 32 | Gola Yoga<br>गोल योग | All the planets are in a single sign. | BPHS ch. 13 (Nabhasa yogas); Brihat Jataka ch. 12 | yoga |

## Other classical yogas and later-tradition doshas (new)

| # | Yoga | What the app checks | Source | Kind |
|---|---|---|---|---|
| 1 | Dharma-Karmadhipati Yoga<br>धर्म-कर्माधिपति योग | The lords of the 9th (fortune) and 10th (work) are together or exchange signs. | BPHS ch. 39 (Raja yogas) | yoga |
| 2 | Maha Parivartana Yoga<br>महा परिवर्तन योग | Two lords of good houses exchange signs. | Phaladeepika ch. 6 (Parivartana yogas) | yoga |
| 3 | Khala Yoga (Parivartana)<br>खल योग (परिवर्तन) | The 3rd lord exchanges signs with the lord of a good house. | Phaladeepika ch. 6 (Parivartana yogas) | yoga |
| 4 | Dainya Yoga (Parivartana)<br>दैन्य योग (परिवर्तन) | The lord of the 6th, 8th or 12th exchanges signs with another lord. | Phaladeepika ch. 6 (Parivartana yogas) | yoga |
| 5 | Lakshmi Yoga *(simplified)*<br>लक्ष्मी योग | The 9th lord is strong in a kendra or trikona and the Lagna lord is well placed. | Phaladeepika ch. 6 | yoga |
| 6 | Saraswati Yoga *(simplified)*<br>सरस्वती योग | Mercury, Jupiter and Venus are in kendras, trikonas or the 2nd, with Jupiter well placed. | Phaladeepika ch. 6 | yoga |
| 7 | Chamara Yoga<br>चामर योग | The Lagna lord is exalted in a kendra and aspected by Jupiter. | Phaladeepika ch. 6 | yoga |
| 8 | Shankha Yoga *(simplified)*<br>शंख योग | The lords of the 5th and 6th are in kendras from each other and the Lagna lord is well placed. | Phaladeepika ch. 6 | yoga |
| 9 | Kahala Yoga *(simplified)*<br>काहल योग | The lords of the 4th and 9th are in kendras from each other and the Lagna lord is well placed. | Phaladeepika ch. 6 | yoga |
| 10 | Bheri Yoga *(simplified)*<br>भेरी योग | Venus, Jupiter and the Lagna lord are in kendras and the 9th lord is strong. | Phaladeepika ch. 6 | yoga |
| 11 | Parvata Yoga *(simplified)*<br>पर्वत योग | A benefic is in a kendra and no malefic occupies the 6th or 8th. | Phaladeepika ch. 6 | yoga |
| 12 | Vasumati Yoga<br>वसुमती योग | Mercury, Jupiter and Venus are all in growth houses (3rd, 6th, 10th, 11th) from the Lagna or the Moon. | Phaladeepika ch. 6 | yoga |
| 13 | Shubha Kartari Yoga<br>शुभ कर्तरी योग | Benefics occupy both the 2nd and 12th houses, enclosing the Lagna. | Phaladeepika ch. 6 | yoga |
| 14 | Papa Kartari<br>पाप कर्तरी | Malefics occupy both the 2nd and 12th houses, hemming in the Lagna. | Phaladeepika ch. 6 | dosha |
| 15 | Lagnadhi Yoga<br>लग्नाधि योग | Mercury, Jupiter and Venus are in the 6th, 7th and 8th from the Lagna. | Phaladeepika ch. 6 | yoga |
| 16 | Guru-Mangala Yoga<br>गुरु-मंगल योग | Jupiter and Mars are together. | Saravali (two-planet combinations) | yoga |
| 17 | Guru-Chandala<br>गुरु-चांडाल | Jupiter is with Rahu. | Later tradition (not in BPHS or Phaladeepika) | dosha |
| 18 | Surya Grahana<br>सूर्य ग्रहण | The Sun is with Rahu or Ketu. | Later tradition (not in BPHS or Phaladeepika) | dosha |
| 19 | Chandra Grahana<br>चंद्र ग्रहण | The Moon is with Rahu or Ketu. | Later tradition (not in BPHS or Phaladeepika) | dosha |
| 20 | Angaraka Yoga<br>अंगारक योग | Mars is with Rahu. | Later tradition (not in BPHS or Phaladeepika) | dosha |
| 21 | Visha Yoga<br>विष योग | The Moon is with Saturn. | Later tradition (not in BPHS or Phaladeepika) | dosha |
| 22 | Kalanidhi Yoga *(simplified)*<br>कलानिधि योग | Jupiter is in the 2nd or 5th, joined or aspected by Mercury and Venus. | Phaladeepika ch. 6 | yoga |
| 23 | Bhaskara Yoga<br>भास्कर योग | Mercury is 2nd from the Sun, the Moon 11th from Mercury and Jupiter in a trine from the Moon. | Phaladeepika ch. 6 | yoga |
| 24 | Marut Yoga<br>मरुत योग | Jupiter is in a trine from Venus, the Moon 5th from Jupiter and the Sun in a kendra from the Moon. | Phaladeepika ch. 6 | yoga |
| 25 | Budha Yoga<br>बुध योग | Jupiter is in the Lagna, the Moon in a kendra from Jupiter, Rahu 2nd from the Moon, and the Sun and Mars 3rd from Rahu. | Phaladeepika ch. 6 | yoga |
| 26 | Indra Yoga<br>इंद्र योग | The lords of the 5th and 11th exchange signs and the Moon is in the 5th. | Phaladeepika ch. 6 | yoga |
| 27 | Shiva Yoga<br>शिव योग | The 5th lord is in the 9th, the 9th lord in the 10th and the 10th lord in the 5th. | Phaladeepika ch. 6 | yoga |
| 28 | Sreenatha Yoga<br>श्रीनाथ योग | The 7th lord is exalted in the 10th and the 10th lord is with the 9th lord. | Phaladeepika ch. 6 | yoga |
| 29 | Khadga Yoga<br>खड्ग योग | The lords of the 2nd and 9th exchange signs and the Lagna lord is in a kendra or trikona. | Phaladeepika ch. 6 | yoga |
| 30 | Jaya Yoga<br>जय योग | The 6th lord is debilitated and the 10th lord exalted. | Phaladeepika ch. 6 | yoga |
| 31 | Trilochana Yoga<br>त्रिलोचन योग | The Sun, Moon and Mars are in trines from each other. | Phaladeepika ch. 6 | yoga |
| 32 | Kurma Yoga *(simplified)*<br>कूर्म योग | Mercury, Jupiter and Venus are in the 5th to 7th, and the Sun, Mars and Saturn in the 1st, 3rd or 11th. | Phaladeepika ch. 6 | yoga |
| 33 | Dhwaja Yoga *(simplified)*<br>ध्वज योग | The Sun, Mars and Saturn are in the 8th and a benefic is in the Lagna. | Saravali (Nabhasa and other yogas) | yoga |
| 34 | Pravrajya Yoga *(simplified)*<br>प्रव्रज्या योग | Four or more planets are in one sign. | Brihat Jataka ch. 15 (Pravrajya) | yoga |
| 35 | Daridra Yoga<br>दरिद्र योग | The 11th lord (gains) is in the 6th, 8th or 12th. | Phaladeepika ch. 6 | yoga |
| 36 | Duryoga<br>दुर्योग | The 10th lord (work) is in the 6th, 8th or 12th. | Phaladeepika ch. 6 | yoga |
| 37 | Kemadruma cancelled<br>केमद्रुम भंग | No planet is next to the Moon, but a planet is in a kendra from the Moon. | Phaladeepika ch. 6 (Kemadruma cancellation) | yoga |
| 38 | Chatussagara Yoga<br>चतुस्सागर योग | Every kendra (1st, 4th, 7th and 10th) has a planet. | Phaladeepika ch. 6 | yoga |
| 39 | Shubhamala Yoga<br>शुभमाला योग | Mercury, Jupiter and Venus occupy the 5th, 6th and 7th houses. | Phaladeepika ch. 6 | yoga |
| 40 | Ashubhamala<br>अशुभमाला | The Sun, Mars and Saturn occupy the 5th, 6th and 7th houses. | Phaladeepika ch. 6 | dosha |
| 41 | Devendra Yoga<br>देवेंद्र योग | The Lagna is a fixed sign, the lords of the 1st and 11th exchange signs, and so do the lords of the 2nd and 10th. | Phaladeepika ch. 6 | yoga |
| 42 | Rajalakshana Yoga<br>राजलक्षण योग | The Moon, Mercury, Jupiter and Venus are all in the Lagna or other kendras. | Phaladeepika ch. 6 | yoga |
