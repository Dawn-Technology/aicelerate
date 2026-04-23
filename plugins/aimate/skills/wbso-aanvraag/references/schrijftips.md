# Schrijftips — Technische Knelpunten en WBSO-taal

Gebruik deze checklist om technische knelpunten en oplossingsrichtingen scherp te formuleren.

---

## 1. De "Niet-Triviaal" Check

> Is het op te lossen door een senior expert die de oplossing direct uit de mouw schudt zonder onderzoek? Dan is het **niet** WBSO-waardig.

Beschrijf altijd waarom de standaardoplossingen, bibliotheken of bestaande technieken in deze
specifieke situatie niet voldoen.

---

## 2. Formuleer het Technisch Knelpunt (het "Waarom?")

**Vermijd functionele termen:**
> ❌ "De website moet sneller laden."

**Gebruik technische termen:**
> ✅ "De huidige database-architectuur veroorzaakt een latency van >500ms bij concurrente schrijfacties van 10.000+ gebruikers; we moeten een nieuw synchronisatieprotocol ontwikkelen."

Stel jezelf de vraag: *Welk technisch principe (informatica, wiskundig model, architectuurbeperking)
staat de gewenste prestatie in de weg?*

---

## 3. De Oplossingsrichting (het "Hoe?")

**Geen stappenplan van werk:**
> ❌ "We gaan coderen en daarna testen."

**Hypothese-gestuurd:**
> ✅ "We onderzoeken of een gedistribueerd caching-algoritme de bottleneck verhelpt, of dat we moeten overstappen op een non-blocking I/O model."

Geef aan dat er **prototypes, testopstellingen of PoC's** nodig zijn om de hypotheses te valideren.

---

## 4. Specifiek voor de Paraplu (de "Gemene Deler")

- **Zoek de rode draad**: Wat is het overkoepelende technische risico dat in alle deelprojecten terugkomt?
- **Afbakening**: Beschrijf duidelijk waar de standaard bouw stopt en waar het onderzoekende deel van de paraplu begint.

---

## 5. WBSO-werkwoorden

**Gebruik:**
analyseren, ontwerpen, modelleren, simuleren, experimenteren, valideren, optimaliseren, prototypen, benchmarken

**Vermijd:**
installeren, configureren, implementeren, bugfixen, deployen, back-ups maken, testen (functioneel)

---

## Zelfevaluatietabel

| ❌ Fout (functioneel / commercieel) | ✅ Goed (technisch / WBSO) |
|-------------------------------------|---------------------------|
| "We maken de machine gebruiksvriendelijker." | "We ontwikkelen een nieuw algoritme voor haptische feedback om de responstijd van de besturing te verlagen naar <10ms." |
| "De app moet op alle telefoons werken." | "Het overwinnen van hardware-specifieke restricties in de geheugenallocatie bij verschillende chipset-architecturen." |
| "We bouwen een koppeling met Systeem X." | "Het ontwikkelen van een abstractielaag voor data-integratie waarbij de integriteit van asynchrone datastromen gewaarborgd blijft." |
