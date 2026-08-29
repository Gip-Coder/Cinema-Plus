1# Seeded Demo Catalog — Data Source Manifest

This document records where the real-world entities seeded by
`scripts/seed_demo_catalog.py` were verified, and when. It exists so the
dataset is auditable: every theatre and movie below is a real, named entity,
not an invented placeholder.

**Verification date for everything in this document: 2026-08-29** (live web
research performed that day against the sources listed).

Only factual notes are recorded here — no copyrighted synopsis/review text
was copied into this repository. Synopses used in the seed data are original
one-line summaries.

**What is NOT verified here:** poster images. No TMDB poster URL could be
independently confirmed during research, so `Movie.poster_url` is left
`NULL` for every seeded movie rather than using a guessed URL.

**What is application-generated, not "real-world" data:** seat layouts,
seat definitions, seat pricing, and the show schedule. These are demo/
operational data associated with a real venue — they are not a claim about
the venue's actual physical seating arrangement or real ticket prices.

---

## Theatres

| Theatre | City | Source(s) | Verified facts |
|---|---|---|---|
| PVR ICON, VR Chennai | Chennai | swarajyamag.com/insta/chennais-movie-experience-gets-better-pvr-icon-equipped-with-world-class-tech-launched-at-anna-nagar; destinationinfinity.org/2018/10/17/pvr-icon-cinemas-vr-mall-anna-nagar; behindwoods.com | 10 screens; one P[XL] RGB-laser + Dolby Atmos screen |
| PVR Palazzo, Forum Vijaya Mall | Chennai | trip.com/travel-guide/attraction/chennai/pvr-palazzo-the-nexus-vijaya-mall-136164476; excellentpublicity.com/cinema/pvr-palazzo-the-forum-vijaya-mall-vadapalani-chennai-tamil-nadu; district.in | 9 screens including 1 IMAX |
| AGS Cinemas, Villivakkam | Chennai | district.in/movies/ags-cinemas-villivakkam-chennai-in-karanodai-CD10184; agscinemas.com/villivakkam.php; joonsquare.com | 5 screens (base/most-cited figure) |
| PVR Nexus Koramangala | Bengaluru | wanderlog.com/place/details/2168477/pvr-cinemas-the-nexus-mall-koramangala; tripadvisor.com (PVR IMAX Bengaluru); en.wikipedia.org/wiki/Nexus_Mall_(Koramangala) | 12 screens; India's first PVR IMAX (now 4K laser), 4DX, Gold Class |
| PVR Orion Mall, Rajajinagar | Bengaluru | cinematreasures.org/theaters/26602; orionmalls.com/orion-mall-at-brigade-gateway/pvr; district.in | 11 screens, ~2,800 seats; PXL, 4DX |
| Prasads Multiplex | Hyderabad | en.wikipedia.org/wiki/Prasads_Multiplex; telanganatoday.com/hyderabads-prasads-is-no-longer-imax; hyderabadtheatres.com/theaters/prasads-multiplex | 6 screens; Screen 6 is large-format "PCX" — explicitly **not** IMAX-branded since 2014 |
| AAA Cinemas, Ameerpet | Hyderabad | hyderabadtheatres.com/theaters/aaa-cinemas; siasat.com/hyderabad-inside-aaa-cinemas-of-allu-arjun-2613231; luv4foodntravel.com | 5 screens; Screen 1 Barco laser + Dolby Atmos, Screen 2 EPIQ Luxon + Atmos |
| PVR Lulu, Edappally | Kochi | wanderlog.com/place/details/144716/pvr-cinemas-lulu-mall; district.in; business-standard.com (confirms IMAX is at Trivandrum, not Kochi) | 9 screens; Gold Class, 4DX; no IMAX at this location |
| PVR Oberon Mall, Edappally | Kochi | facebook.com/OberonMall (rebrand announcement); oberonmall.com/movies; en.wikipedia.org/wiki/Oberon_Mall | 4 screens; Dolby 7.1; originally Cinemax, Kerala's first multiplex (2010) |
| Cinepolis, Fun Republic Mall | Coimbatore | district.in/movies/cinepolis-fun-cinema-republic-mall-peelamedu-coimbatore; funrepublic.in/coimbatore-cinepolis1.php; en.wikipedia.org/wiki/Fun_Republic_Mall_(Coimbatore) | 5 screens, ~1,119 seats |
| Miraj Cinemas, Bhupathi Surya Central | Visakhapatnam | x.com/MirajCinemas/status/1839195732156276868 (opening announcement); ticketnew.com; en.wikipedia.org/wiki/CENTRAL,_Visakhapatnam | 4 screens |
| INOX, CMR Central | Visakhapatnam | yovizag.com (opening coverage, first INOX in Vizag); district.in; en.wikipedia.org/wiki/CMR_Central,_Visakhapatnam | 4 screens |
| PVR, Phoenix Marketcity | Mumbai | district.in/movies/pvr-market-city-kurla-w-mumbai-in-mumbai-CD1022270; justdial.com; phoenixmarketcity.com/mumbai/brand/PVR/257 | 14 screens |
| INOX, Nehru Place | New Delhi | district.in/movies/inox-nehru-place-district-centre-new-delhi; theatresdb.com/delhi/nehru-place/inox-nehru-place; justdial.com | 5 screens, opened March 2018 |
| PVR Priya, Vasant Vihar | New Delhi | businesstoday.in/latest/corporate/story/pvr-priya-delhis-iconic-theatre-gets-a-luxury-makeover-305453-2021-08-29; businessbioscopes.com/pvr-priya; en.wikipedia.org/wiki/PVR_INOX | 1 screen; historic founding site of the PVR brand (1997), now standalone IMAX-with-laser |
| PVR Superplex, Logix City Centre | Noida | district.in/movies/pvr-superplex-logix-sector-32-noida; businessbioscopes.com/pvr-logix-noida; nearbuy.com | 15 screens; IMAX (largest in NCR), 4DX, PXL, Gold |
| City Pride Multiplex, Kothrud | Pune | tripadvisor.in (City Pride Multiplex Pune); justdial.com; magicpin.in | 7 screens (renovated); Dolby digital, recliner seating |
| Nandan | Kolkata | cinematreasures.org/theaters/68077; en.wikipedia.org/wiki/Nandan_(Kolkata); icad.wb.gov.in/venue-wise-schedule/nandan | 3 screens (Nandan I/II/III); Govt. of West Bengal, opened 1985 by Satyajit Ray |
| Cinepolis, Alpha One Mall | Ahmedabad | cinematreasures.org/theaters/59170; paytm.com/movies/ahmedabad/cinepolis-nexus-one-ahmedabad-c/125; mappls.com | Screen count disputed across sources (4–6); Dolby 7.1, RealD 3D |
| Raj Mandir Cinema | Jaipur | en.wikipedia.org/wiki/Raj_Mandir_Cinema; district.in/movies/rajmandir-cinema-dolby-atmos-panch-batti-jaipur | 1 screen, 854 seats, opened June 1, 1976 |
| PVR Superplex, Lulu Mall | Lucknow | business-standard.com/article/companies/pvr-launches-lucknow-s-biggest-11-screen-cinema-post-merger-with-inox-123030600436_1.html; indiaretailing.com/2023/03/03/pvr-cinemas-launches-11-screen-multiplex-in-lucknow; marketscreener.com | 11 screens (opened March 2023); 4DX, PXL, 2× LUXE |
| PVR, Elante Mall | Chandigarh | tricity.in/pvr-elante; wowchandigarh.com/best-entertainment/multiplexes/pvr-elante-mall; chandigarhbuzz.com | 8 screens; IMAX, 4DX |

**Investigated but excluded** (insufficient/contradictory verification): INOX Garuda Mall (Bengaluru — screen count sources contradict, 3 vs 34); PVR Sathyam, Royapettah (Chennai — real venue, no reliable screen count found); "PVR World Trade Park, Jaipur" (does not exist — that property is Cinepolis, unverified); PVR Mall of Jaipur (real, operating, but no source gave a screen count); a 3rd Coimbatore venue.

## Movies

| Title | Language | Release Date | Status (as of 2026-08-29) | Source(s) | Notes |
|---|---|---|---|---|---|
| The Godfather | English | 1972-03-24 | Released | themoviedb.org/movie/238; imdb.com/title/tt0068646 | Rating recalled, not re-confirmed live this session — lower confidence |
| The Matrix | English | 1999-03-31 | Released | imdb.com/title/tt0133093; themoviedb.org/movie/603 | Fully verified live |
| Titanic | English | 1997-12-19 | Released | imdb.com/title/tt0120338; themoviedb.org/movie/597 | Verified live |
| Jurassic Park | English | 1993-06-11 | Released | imdb.com/title/tt0107290; en.wikipedia.org/wiki/Jurassic_Park_(film) | Verified live |
| The Dark Knight | English | 2008-07-18 | Released | imdb.com/title/tt0468569; themoviedb.org/movie/155 | Verified live |
| Inception | English | 2010-07-16 | Released | imdb.com/title/tt1375666 | Verified live |
| Interstellar | English | 2014-11-07 | Released | imdb.com/title/tt0816692 | Verified live |
| Top Gun: Maverick | English | 2022-05-25 | Released | imdb.com/title/tt1745960; themoviedb.org/movie/361743 | Verified live |
| Barbie | English | 2023-07-21 | Released | imdb.com/title/tt1517268; themoviedb.org/movie/346698 | Verified live |
| Oppenheimer | English | 2023-07-21 | Released | imdb.com/title/tt15398776; themoviedb.org/movie/872585 | Verified live |
| Dune: Part Two | English | 2024-03-01 | Released | themoviedb.org/movie/693134; boxofficemojo.com/title/tt15239678 | Rating from a secondary snippet, moderate confidence |
| Deadpool & Wolverine | English | 2024-07-26 | Released | imdb.com/title/tt6263850; themoviedb.org/movie/533535 | Verified live |
| Inside Out 2 | English | 2024-06-11 | Released | imdb.com/title/tt22022452; themoviedb.org/movie/1022789 | Verified live |
| Twisters | English | 2024-07-19 | Released | imdb.com/title/tt12584954; themoviedb.org/movie/718821 | Rating not found live — left `NULL`, not guessed |
| Wicked | English | 2024-11-22 | Released | imdb.com/title/tt1262426; en.wikipedia.org/wiki/Wicked_(2024_film) | Verified live |
| Sinners | English | 2025-04-18 | Released | en.wikipedia.org/wiki/Sinners_(2025_film); imdb.com/news/ni65258769 | Verified live |
| A Minecraft Movie | English | 2025-04-04 | Released | imdb.com/title/tt3566834; themoviedb.org/movie/950387 | Verified live |
| F1: The Movie | English | 2025-06-27 | Released | imdb.com/title/tt16311594; en.wikipedia.org/wiki/F1_(film) | Verified live |
| Superman | English | 2025-07-11 | Released | imdb.com/title/tt5950044; themoviedb.org/movie/1061474 | Verified live |
| Mission: Impossible – The Final Reckoning | English | 2025-05-23 | Released | imdb.com/title/tt9603208; en.wikipedia.org/wiki/Mission:_Impossible_–_The_Final_Reckoning | Verified live |
| Zootopia 2 | English | 2025-11-26 | Released | imdb.com/title/tt26443597; deadline.com (Nov 2025) | Runtime/rating confirmed on follow-up pass |
| Avatar: Fire and Ash | English | 2025-12-19 | Released | imdb.com/title/tt1757678; avatar.com/movies/avatar-fire-and-ash | Rating confirmed on follow-up pass |
| Spider-Man: Brand New Day | English | 2026-07-31 | Released | imdb.com/title/tt22084616; marvel.com/movies/spider-man-brand-new-day; forbes.com (Aug 2026) | Initially misflagged as upcoming; corrected after verifying it already released before 2026-08-29 |
| Avengers: Doomsday | English | 2026-12-18 | **Upcoming** | imdb.com/news/ni65298698; marvel.com/movies/avengers-doomsday | Confirmed after a prior delay; date is after 2026-08-29 |
| Avengers: Secret Wars | English | 2027-12-17 | **Upcoming** | imdb.com/news/ni65298698 | — |
| The Batman: Part II | English | 2028-02-18 | **Upcoming** | hollywoodreporter.com; variety.com (2026 delay coverage); empireonline.com | Date has slipped multiple times — re-verify before relying on it long-term |
| Sholay | Hindi | 1975-08-15 | Released | imdb.com/title/tt0073707; en.wikipedia.org/wiki/Sholay | Verified live |
| Nayakan | Tamil | 1987-10-21 | Released | imdb.com/title/tt0093603; en.wikipedia.org/wiki/Nayakan | Verified live |
| Baasha | Tamil | 1995-01-12 | Released | imdb.com/title/tt0139876; en.wikipedia.org/wiki/Baashha | Verified live |
| Dilwale Dulhania Le Jayenge | Hindi | 1995-10-20 | Released | imdb.com/title/tt0112870; en.wikipedia.org/wiki/Dilwale_Dulhania_Le_Jayenge | Verified live |
| Lagaan | Hindi | 2001-06-15 | Released | imdb.com/title/tt0169102; en.wikipedia.org/wiki/Lagaan | Verified live |
| Magadheera | Telugu | 2009-07-31 | Released | imdb.com/title/tt1447500; en.wikipedia.org/wiki/Magadheera | Verified live |
| 3 Idiots | Hindi | 2009-12-25 | Released | imdb.com/title/tt1187043; en.wikipedia.org/wiki/3_Idiots | Verified live |
| Drishyam | Malayalam | 2013-12-19 | Released | imdb.com/title/tt3417422; en.wikipedia.org/wiki/Drishyam | Verified live |
| Kantara | Kannada | 2022-09-30 | Released | en.wikipedia.org/wiki/Kantara_(2022_film) | Rating not confirmed live (WebFetch to IMDb blocked) — left `NULL` |
| Manjummel Boys | Malayalam | 2024-02-22 | Released | imdb.com/title/tt26458038; en.wikipedia.org/wiki/Manjummel_Boys | Verified live |
| Kalki 2898 AD | Telugu | 2024-06-27 | Released | imdb.com/title/tt12735488 | Runtime not confirmed — left `NULL` |
| Stree 2: Sarkate Ka Aatank | Hindi | 2024-08-15 | Released | imdb.com/title/tt27510174; en.wikipedia.org/wiki/Stree_2 | Runtime not confirmed — left `NULL` |
| Pushpa 2: The Rule | Telugu | 2024-12-05 | Released | imdb.com/title/tt16539454; en.wikipedia.org/wiki/Pushpa_2:_The_Rule | Verified live |
| Sitaare Zameen Par | Hindi | 2025-06-20 | Released | imdb.com/title/tt29471573; en.wikipedia.org/wiki/Sitaare_Zameen_Par | Verified live |
| Thug Life | Tamil | 2025-06-05 | Released | en.wikipedia.org/wiki/Thug_Life_(2025_film) | Verified live |
| Kannappa | Telugu | 2025-06-27 | Released | en.wikipedia.org/wiki/Kannappa_(film) | Verified live |
| Coolie | Tamil | 2025-08-14 | Released | en.wikipedia.org/wiki/Coolie_(2025_film) | Rating disputed across sources (6.0–6.8) — left `NULL` rather than guess |
| Lokah Chapter 1: Chandra | Malayalam | 2025-08-28 | Released | imdb.com/title/tt33372494; en.wikipedia.org/wiki/Lokah_Chapter_1:_Chandra | Verified live; highest-grossing Malayalam film ever |
| Kantara: Chapter 1 | Kannada | 2025-10-02 | Released | imdb.com/title/tt26439764; en.wikipedia.org/wiki/Kantara:_Chapter_1 | Runtime not confirmed — left `NULL` |
| Toxic | Kannada | 2026-08-26 | Released (3 days before verification date) | en.wikipedia.org/wiki/Toxic_(2026_film) | Too new for a stable rating — left `NULL` |
| Jailer 2 | Tamil | 2026-10-15 | **Upcoming** | en.wikipedia.org/wiki/Jailer_2 | Confirmed still future relative to 2026-08-29 |
| Spirit | Telugu | 2027-03-05 | **Upcoming** | bollywoodhungama.com; sacnilk.com | Confirmed still future relative to 2026-08-29 |

**Excluded from "upcoming"**: several Hindi/Tamil/Telugu titles that stale listicles labeled "upcoming" but which live verification showed had release dates in January–May 2026 (already passed as of the 2026-08-29 verification date) were deliberately left out rather than mislabeled.
