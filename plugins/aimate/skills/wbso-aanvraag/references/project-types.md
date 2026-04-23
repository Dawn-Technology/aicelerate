# WBSO Projecttypen — Keuzehulp

## Overzicht

| Projecttype | Wanneer van toepassing |
|-------------|----------------------|
| **Ontwikkelingsproject Programmatuur** | Softwareontwikkeling met technische nieuwheid (algoritmen, architectuur, AI/ML, nieuwe protocollen) |
| **Ontwikkelingsproject Fysiek Product/Proces** | Hardware, mechatronica, productieproces, embedded systemen met firmware als onderdeel |
| **Technisch-Wetenschappelijk Onderzoek (TWO)** | Fundamenteel of toegepast onderzoek zonder vooraf bepaald eindproduct |

---

## Type 1: Ontwikkelingsproject Programmatuur

### Wanneer kiezen?
- Het eindresultaat is primair software (SaaS, API, platform, app, algoritme).
- Er is sprake van technische nieuwheid in de software-architectuur, algoritmen, of data-verwerking.
- Het project gaat verder dan integreren van bestaande frameworks.

### Typische WBSO-waardige activiteiten
- Ontwikkelen van een nieuw algoritme of ML-model
- Bouwen van een nieuwe softwarearchitectuur voor een technisch onopgelost probleem
- Onderzoek naar performance-optimalisaties die niet met standaard technieken bereikt worden
- Ontwikkelen van nieuwe compressie-, encryptie- of communicatieprotocollen
- Technisch onderzoek naar integratie van tegenstrijdige systemen

### Niet WBSO-waardig (voor dit type)
- Bouwen van CRUD-functionaliteit op bestaande frameworks
- UI/UX design en implementatie
- Integratie van API's volgens bestaande documentatie
- Migratie van data of systemen
- Configuratie van cloud-infrastructuur

### Sleutelvraag voor formulier
> "Wat is de technische innovatie in de software die niet met bestaande kennis of tools gerealiseerd kan worden?"

---

## Type 2: Ontwikkelingsproject Fysiek Product/Proces

### Wanneer kiezen?
- Het eindresultaat heeft een fysieke component (hardware, apparaat, machine, productielijn).
- Software is slechts een onderdeel van een groter fysiek systeem.

### Typische WBSO-waardige activiteiten
- Ontwerpen van nieuwe sensortechnologie of actuatoren
- Ontwikkelen van embedded firmware voor nieuwe hardware
- Onderzoek naar nieuwe materialen of productieprocessen
- Technisch ontwerp van mechatronische systemen

---

## Type 3: Technisch-Wetenschappelijk Onderzoek (TWO)

### Wanneer kiezen?
- Het doel is kennisverwerving, niet een concreet product.
- De uitkomst is onzeker: het kan zijn dat het onderzoek geen bruikbaar eindproduct oplevert.
- Er zijn hypotheses die systematisch getest worden.

### Typische WBSO-waardige activiteiten
- Fundamenteel onderzoek naar een technisch fenomeen
- Proof-of-concept onderzoek waarbij het eindresultaat onbekend is
- Benchmarkonderzoek naar nieuwe technologieën

---

## Beslisboom

```
Is het eindresultaat primair software?
├── JA → Is er een concrete eindgebruikerstoepassing voorzien?
│         ├── JA → Ontwikkelingsproject Programmatuur
│         └── NEE → Technisch-Wetenschappelijk Onderzoek
└── NEE → Is er een fysiek product of productieproces?
          ├── JA → Ontwikkelingsproject Fysiek Product/Proces
          └── NEE → Technisch-Wetenschappelijk Onderzoek
```
