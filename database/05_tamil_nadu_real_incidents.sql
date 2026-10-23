USE disaster_response;

-- 50 historical Tamil Nadu disaster event/location records.
-- Source URLs are included in descriptions for verification.
-- Coordinates are approximate map points.
-- people_affected = 0 means the location-specific count is unknown.
-- severity_hint is a project classification, not an official rating.

START TRANSACTION;

INSERT INTO disasters
(title, disaster_type, description, address, latitude, longitude,
 people_affected, severity_hint, status, reported_by_id)
VALUES

-- 1-6: Original six historical events

('Chennai Floods - December 2015', 'flood',
 'Severe flooding affected Chennai and surrounding areas in November-December 2015. A location-specific affected-person count is not provided. Source: https://www.niti.gov.in/node/328',
 'Chennai, Tamil Nadu, India', 13.0827, 80.2707, 0, 'critical', 'resolved', NULL),

('Cyclone Vardah - December 2016', 'cyclone',
 'Cyclone Vardah crossed the north Tamil Nadu coast near Chennai on 12 December 2016. Source: https://ndrf.gov.in/en/operations/cyclone-vardah-tamil-nadu-andhra-pradesh-and-pudduchery-dec-2016',
 'Chennai, Tamil Nadu, India', 13.0827, 80.2707, 0, 'critical', 'resolved', NULL),

('Cyclone Gaja - November 2018', 'cyclone',
 'Cyclone Gaja affected coastal districts of Tamil Nadu in November 2018. Nagapattinam is used as the mapped location. Source: https://eparlib.sansad.in/bitstream/123456789/808821/1/14714.pdf',
 'Nagapattinam, Tamil Nadu, India', 10.7672, 79.8449, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar - November 2020', 'cyclone',
 'Very Severe Cyclonic Storm Nivar crossed the Tamil Nadu-Puducherry coast during 25-26 November 2020. Source: https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=1675844&lang=2&reg=48',
 'Cuddalore, Tamil Nadu, India', 11.7447, 79.7680, 0, 'critical', 'resolved', NULL),

('Cyclone Michaung - December 2023', 'cyclone',
 'Cyclone Michaung brought heavy rainfall and flooding impacts to Chennai and Tiruvallur districts. Source: https://ndrf.gov.in/en/operations/cyclone-michaung',
 'Chennai, Tamil Nadu, India', 13.0827, 80.2707, 0, 'critical', 'resolved', NULL),

('Cyclone Fengal - November-December 2024', 'cyclone',
 'Cyclone Fengal affected northern Tamil Nadu and nearby coastal areas in late November and early December 2024. Source: https://www.ndrf.gov.in/en/operations/severe-cyclonic-storm-fengal',
 'Villupuram, Tamil Nadu, India', 11.9401, 79.4861, 0, 'critical', 'resolved', NULL),

-- 7-10: Additional locations associated with the 2015 floods

('Tamil Nadu Floods 2015 - Cuddalore', 'flood',
 'The November 2015 heavy-rainfall spells caused extensive damage in Cuddalore district. Source: https://www.niti.gov.in/node/328',
 'Cuddalore, Tamil Nadu, India', 11.7447, 79.7680, 0, 'critical', 'resolved', NULL),

('Tamil Nadu Floods 2015 - Kancheepuram', 'flood',
 'Kancheepuram town was severely affected during the November 2015 heavy-rainfall spells. Source: https://www.niti.gov.in/node/328',
 'Kancheepuram, Tamil Nadu, India', 12.8342, 79.7036, 0, 'critical', 'resolved', NULL),

('Tamil Nadu Floods 2015 - Tiruvallur', 'flood',
 'Heavy rainfall and flooding affected Tiruvallur district during the November-December 2015 event. Source: https://www.niti.gov.in/node/328',
 'Tiruvallur, Tamil Nadu, India', 13.1439, 79.9089, 0, 'critical', 'resolved', NULL),

('Tamil Nadu Floods 2015 - Chennai Metropolitan Area', 'flood',
 'The December 2015 flood inundated low-lying areas of Chennai and caused major disruption. Source: https://www.cag.gov.in/ag2/tamil-nadu/en/audit-report/details/45722',
 'Chennai Metropolitan Area, Tamil Nadu, India', 13.0827, 80.2707, 0, 'critical', 'resolved', NULL),

-- 11-15: October 2005 deep depression rainfall locations

('October 2005 Heavy Rain - Chennai', 'flood',
 'Heavy rainfall associated with a deep depression was recorded in the Chennai area in October 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Chennai, Tamil Nadu, India', 13.0827, 80.2707, 0, 'high', 'resolved', NULL),

('October 2005 Heavy Rain - Tiruvallur', 'flood',
 'Heavy rainfall associated with a deep depression was recorded in the Tiruvallur area in October 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Tiruvallur, Tamil Nadu, India', 13.1439, 79.9089, 0, 'high', 'resolved', NULL),

('October 2005 Heavy Rain - Red Hills', 'flood',
 'Heavy rainfall associated with a deep depression was recorded at Red Hills in October 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Red Hills, Chennai, Tamil Nadu, India', 13.1946, 80.2051, 0, 'high', 'resolved', NULL),

('October 2005 Heavy Rain - Ponneri', 'flood',
 'Heavy rainfall associated with a deep depression was recorded at Ponneri in October 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Ponneri, Tiruvallur district, Tamil Nadu, India', 13.3387, 80.1948, 0, 'high', 'resolved', NULL),

('October 2005 Heavy Rain - Tambaram', 'flood',
 'Heavy rainfall associated with a deep depression was recorded at Tambaram in October 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Tambaram, Chennai, Tamil Nadu, India', 12.9249, 80.1000, 0, 'high', 'resolved', NULL),

-- 16-25: Cyclone Baaz - December 2005 rainfall locations

('Cyclone Baaz 2005 - Tambaram', 'cyclone',
 'IMD records significant rainfall at Tambaram associated with Cyclone Baaz in December 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Tambaram, Chennai, Tamil Nadu, India', 12.9249, 80.1000, 0, 'high', 'resolved', NULL),

('Cyclone Baaz 2005 - Chennai', 'cyclone',
 'IMD records significant rainfall in Chennai associated with Cyclone Baaz in December 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Chennai, Tamil Nadu, India', 13.0827, 80.2707, 0, 'high', 'resolved', NULL),

('Cyclone Baaz 2005 - Tiruvallur', 'cyclone',
 'IMD records significant rainfall in the Tiruvallur area associated with Cyclone Baaz in December 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Tiruvallur, Tamil Nadu, India', 13.1439, 79.9089, 0, 'high', 'resolved', NULL),

('Cyclone Baaz 2005 - Red Hills', 'cyclone',
 'IMD records significant rainfall at Red Hills associated with Cyclone Baaz in December 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Red Hills, Chennai, Tamil Nadu, India', 13.1946, 80.2051, 0, 'high', 'resolved', NULL),

('Cyclone Baaz 2005 - Arakkonam', 'cyclone',
 'IMD records significant rainfall at Arakkonam associated with Cyclone Baaz in December 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Arakkonam, Ranipet district, Tamil Nadu, India', 13.0845, 79.6700, 0, 'high', 'resolved', NULL),

('Cyclone Baaz 2005 - Sriperumbudur', 'cyclone',
 'IMD records significant rainfall at Sriperumbudur associated with Cyclone Baaz in December 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Sriperumbudur, Kancheepuram district, Tamil Nadu, India', 12.9675, 79.9410, 0, 'high', 'resolved', NULL),

('Cyclone Baaz 2005 - Chengalpattu', 'cyclone',
 'IMD records significant rainfall at Chengalpattu associated with Cyclone Baaz in December 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Chengalpattu, Tamil Nadu, India', 12.6819, 79.9888, 0, 'high', 'resolved', NULL),

('Cyclone Baaz 2005 - Tiruttani', 'cyclone',
 'IMD records significant rainfall at Tiruttani associated with Cyclone Baaz in December 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Tiruttani, Tiruvallur district, Tamil Nadu, India', 13.1759, 79.6160, 0, 'high', 'resolved', NULL),

('Cyclone Baaz 2005 - Poondi', 'cyclone',
 'IMD records significant rainfall at Poondi associated with Cyclone Baaz in December 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Poondi, Tiruvallur district, Tamil Nadu, India', 13.2050, 79.8950, 0, 'high', 'resolved', NULL),

('Cyclone Baaz 2005 - Ponneri', 'cyclone',
 'IMD records significant rainfall at Ponneri associated with Cyclone Baaz in December 2005. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Ponneri, Tiruvallur district, Tamil Nadu, India', 13.3387, 80.1948, 0, 'high', 'resolved', NULL),

-- 26-28: Cyclone Ogni - October 2006

('Cyclone Ogni 2006 - Chennai', 'cyclone',
 'IMD records significant rainfall in Chennai associated with Cyclone Ogni in October 2006. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Chennai, Tamil Nadu, India', 13.0827, 80.2707, 0, 'high', 'resolved', NULL),

('Cyclone Ogni 2006 - Tiruvallur', 'cyclone',
 'IMD records significant rainfall in Tiruvallur associated with Cyclone Ogni in October 2006. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Tiruvallur, Tamil Nadu, India', 13.1439, 79.9089, 0, 'high', 'resolved', NULL),

('Cyclone Ogni 2006 - Red Hills', 'cyclone',
 'IMD records significant rainfall at Red Hills associated with Cyclone Ogni in October 2006. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Red Hills, Chennai, Tamil Nadu, India', 13.1946, 80.2051, 0, 'high', 'resolved', NULL),

-- 29-37: Additional documented Cyclone Vardah rainfall locations

('Cyclone Vardah 2016 - Kancheepuram', 'cyclone',
 'IMD records heavy rainfall in Kancheepuram district associated with Cyclone Vardah in December 2016. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Kancheepuram, Tamil Nadu, India', 12.8342, 79.7036, 0, 'critical', 'resolved', NULL),

('Cyclone Vardah 2016 - Poonamallee', 'cyclone',
 'IMD records heavy rainfall at Poonamallee associated with Cyclone Vardah in December 2016. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Poonamallee, Chennai, Tamil Nadu, India', 13.0480, 80.0940, 0, 'critical', 'resolved', NULL),

('Cyclone Vardah 2016 - Chembarambakkam', 'cyclone',
 'IMD records heavy rainfall at Chembarambakkam associated with Cyclone Vardah in December 2016. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Chembarambakkam, Tiruvallur district, Tamil Nadu, India', 13.0100, 80.0600, 0, 'critical', 'resolved', NULL),

('Cyclone Vardah 2016 - Sriperumbudur', 'cyclone',
 'IMD records heavy rainfall at Sriperumbudur associated with Cyclone Vardah in December 2016. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Sriperumbudur, Kancheepuram district, Tamil Nadu, India', 12.9675, 79.9410, 0, 'critical', 'resolved', NULL),

('Cyclone Vardah 2016 - Tambaram', 'cyclone',
 'IMD records heavy rainfall at Tambaram associated with Cyclone Vardah in December 2016. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Tambaram, Chennai, Tamil Nadu, India', 12.9249, 80.1000, 0, 'critical', 'resolved', NULL),

('Cyclone Vardah 2016 - Meenambakkam', 'cyclone',
 'IMD records heavy rainfall at Meenambakkam associated with Cyclone Vardah in December 2016. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Meenambakkam, Chennai, Tamil Nadu, India', 12.9941, 80.1709, 0, 'critical', 'resolved', NULL),

('Cyclone Vardah 2016 - Nungambakkam', 'cyclone',
 'IMD records heavy rainfall at Nungambakkam associated with Cyclone Vardah in December 2016. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Nungambakkam, Chennai, Tamil Nadu, India', 13.0569, 80.2425, 0, 'critical', 'resolved', NULL),

('Cyclone Vardah 2016 - Kattukuppam', 'cyclone',
 'IMD records heavy rainfall at Kattukuppam associated with Cyclone Vardah in December 2016. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Kattukuppam, Kancheepuram district, Tamil Nadu, India', 12.8500, 80.2500, 0, 'critical', 'resolved', NULL),

('Cyclone Vardah 2016 - Chembarambakkam Reservoir Area', 'cyclone',
 'The Chembarambakkam area recorded heavy rainfall during Cyclone Vardah in December 2016. This is a separate mapped-area record, not a separate cyclone. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Chembarambakkam reservoir area, Tamil Nadu, India', 13.0100, 80.0600, 0, 'critical', 'resolved', NULL),

-- 38-50: Additional documented Cyclone Nivar rainfall locations

('Cyclone Nivar 2020 - Chennai Nungambakkam', 'cyclone',
 'IMD records heavy rainfall at Nungambakkam during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Nungambakkam, Chennai, Tamil Nadu, India', 13.0569, 80.2425, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - Meenambakkam', 'cyclone',
 'IMD records heavy rainfall at Meenambakkam during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Meenambakkam, Chennai, Tamil Nadu, India', 12.9941, 80.1709, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - Sholinganallur', 'cyclone',
 'IMD records heavy rainfall at Sholinganallur during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Sholinganallur, Chennai, Tamil Nadu, India', 12.9010, 80.2279, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - Taramani', 'cyclone',
 'IMD records heavy rainfall at Taramani during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Taramani, Chennai, Tamil Nadu, India', 12.9867, 80.2488, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - DGP Office Area', 'cyclone',
 'IMD records heavy rainfall in the DGP Office area during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'DGP Office area, Chennai, Tamil Nadu, India', 13.0400, 80.2500, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - MGR Nagar', 'cyclone',
 'IMD records heavy rainfall at MGR Nagar during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'MGR Nagar, Chennai, Tamil Nadu, India', 13.0180, 80.2010, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - Mahabalipuram', 'cyclone',
 'IMD records heavy rainfall at Mahabalipuram during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Mahabalipuram, Chengalpattu district, Tamil Nadu, India', 12.6208, 80.1945, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - Alandur', 'cyclone',
 'IMD records heavy rainfall at Alandur during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Alandur, Chennai, Tamil Nadu, India', 12.9975, 80.2006, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - Puzhal', 'cyclone',
 'IMD records heavy rainfall at Puzhal during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Puzhal, Chennai, Tamil Nadu, India', 13.1600, 80.2040, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - Chembarambakkam', 'cyclone',
 'IMD records heavy rainfall at Chembarambakkam during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Chembarambakkam, Tamil Nadu, India', 13.0100, 80.0600, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - Thamaraipakkam', 'cyclone',
 'IMD records heavy rainfall at Thamaraipakkam during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Thamaraipakkam, Tiruvallur district, Tamil Nadu, India', 13.2400, 79.8700, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - Pallipattu', 'cyclone',
 'IMD records heavy rainfall at Pallipattu during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Pallipattu, Tiruvallur district, Tamil Nadu, India', 13.3380, 79.4440, 0, 'critical', 'resolved', NULL),

('Cyclone Nivar 2020 - Cholavaram', 'cyclone',
 'IMD records heavy rainfall at Cholavaram during Cyclone Nivar in November 2020. Source: https://rsmcnewdelhi.imd.gov.in/download.php?path=uploads%2Freport%2F26%2F26_0580dd_Michaung+Report_Final_Sir.pdf',
 'Cholavaram, Tiruvallur district, Tamil Nadu, India', 13.2300, 80.1600, 0, 'critical', 'resolved', NULL);

COMMIT;