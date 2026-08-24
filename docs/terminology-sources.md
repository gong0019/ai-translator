# Curated terminology sources

The files in `skills/*_terms.json` are a small, curated translation layer, not a copied dictionary. Terms are normalized against the following public reference sources and then reviewed for the supported translation languages.

- Finance and economics: [IMF Terminology](https://www.imf.org/en/about/terminology) and the [IMF Glossary](https://www.imf.org/en/about/glossary).
- Securities and equities: [U.S. SEC Glossary of Terms](https://www.sec.gov/file/glossary-terms-0).
- Computing and cybersecurity: [NIST CSRC Glossary](https://csrc.nist.gov/glossary) and [NISTIR 7298 Rev. 3](https://doi.org/10.6028/NIST.IR.7298r3).
- Blockchain: terminology is aligned with the [Bitcoin Developer Guide](https://developer.bitcoin.org/devguide/) and established protocol usage; ambiguous words such as `wallet` and `mining` require a blockchain context marker before they are injected.

The catalog intentionally stores translations rather than source definitions. Additions should use the canonical record shape shown below and should be checked against an authoritative domain source before inclusion.

```json
{
  "en": "quantitative easing",
  "zh": "量化宽松",
  "ja": "量的緩和",
  "ko": "양적 완화",
  "de": "quantitative Lockerung",
  "fr": "assouplissement quantitatif",
  "es": "flexibilización cuantitativa",
  "ru": "количественное смягчение",
  "it": "allentamento quantitativo"
}
```
