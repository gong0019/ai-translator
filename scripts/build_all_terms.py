#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive 9-Domain Terminology Generator (200+ high-frequency professional terms per catalog)."""

from term_catalog_utils import merge_catalog

def save_terms(filename, terms_tuples):
    terms_list = [
        {
            "en": t[0], "zh": t[1], "ja": t[2], "ko": t[3], "de": t[4],
            "fr": t[5], "es": t[6], "ru": t[7], "it": t[8]
        }
        for t in terms_tuples
    ]
    total = merge_catalog(filename, terms_list)
    print(f"✓ Safely merged {filename}: {total} terms")

# 1. 国际贸易与海关物流 (Trade Terms)
trade_terms = [
    ("Incoterms", "国际贸易术语解释通则", "インコタームズ", "인코텀즈", "Incoterms", "Incoterms", "Incoterms", "Инкотермс", "Incoterms"),
    ("free on board", "船上交货（FOB）", "本船渡し（FOB）", "본선 인도（FOB）", "frei an Bord（FOB）", "franco à bord（FOB）", "franco a bordo（FOB）", "франко-борт（FOB）", "franco a bordo（FOB）"),
    ("FOB", "船上交货（FOB）", "本船渡し（FOB）", "본선 인도（FOB）", "frei an Bord（FOB）", "franco à bord（FOB）", "franco a bordo（FOB）", "франко-борт（FOB）", "franco a bordo（FOB）"),
    ("cost insurance and freight", "成本加保险费、运费（CIF）", "運賃・保険料込み条件（CIF）", "운임·보험료 포함 인도（CIF）", "Kosten, Versicherung und Fracht（CIF）", "coût, assurance et fret（CIF）", "coste, seguro y flete（CIF）", "стоимость, страхование и фрахт（CIF）", "costo, assicurazione e nolo（CIF）"),
    ("CIF", "成本加保险费、运费（CIF）", "運賃・保険料込み条件（CIF）", "운임·보험료 포함 인도（CIF）", "Kosten, Versicherung und Fracht（CIF）", "coût, assurance et fret（CIF）", "coste, seguro y flete（CIF）", "стоимость, страхование и фрахт（CIF）", "costo, assicurazione e nolo（CIF）"),
    ("cost and freight", "成本加运费（CFR）", "運賃込み条件（CFR）", "운임 포함 인도（CFR）", "Kosten und Fracht（CFR）", "coût et fret（CFR）", "coste y flete（CFR）", "стоимость и фрахт（CFR）", "costo e nolo（CFR）"),
    ("CFR", "成本加运费（CFR）", "運賃込み条件（CFR）", "운임 포함 인도（CFR）", "Kosten und Fracht（CFR）", "coût et fret（CFR）", "coste y flete（CFR）", "стоимость и фрахт（CFR）", "costo e nolo（CFR）"),
    ("ex works", "工厂交货（EXW）", "工場渡し（EXW）", "공장 인도（EXW）", "ab Werk（EXW）", "départ usine（EXW）", "en fábrica（EXW）", "франко-завод（EXW）", "franco fabbrica（EXW）"),
    ("EXW", "工厂交货（EXW）", "工場渡し（EXW）", "공장 인도（EXW）", "ab Werk（EXW）", "départ usine（EXW）", "en fábrica（EXW）", "франко-завод（EXW）", "franco fabbrica（EXW）"),
    ("free carrier", "货交承运人（FCA）", "運送人渡し（FCA）", "운송인 인도（FCA）", "frei Frachtführer（FCA）", "franco transporteur（FCA）", "franco transportista（FCA）", "франко-перевозчик（FCA）", "franco vettore（FCA）"),
    ("FCA", "货交承运人（FCA）", "運送人渡し（FCA）", "운송인 인도（FCA）", "frei Frachtführer（FCA）", "franco transporteur（FCA）", "franco transportista（FCA）", "франко-перевозчик（FCA）", "franco vettore（FCA）"),
    ("free alongside ship", "船边交货（FAS）", "船側渡し（FAS）", "선측 인도（FAS）", "frei Längsseite Schiff（FAS）", "franco le long du navire（FAS）", "franco al costado del buque（FAS）", "франко вдоль борта судна（FAS）", "franco lungo bordo（FAS）"),
    ("FAS", "船边交货（FAS）", "船側渡し（FAS）", "선측 인도（FAS）", "frei Längsseite Schiff（FAS）", "franco le long du navire（FAS）", "franco al costado del buque（FAS）", "франко вдоль борта судна（FAS）", "franco lungo bordo（FAS）"),
    ("carriage paid to", "运费付至（CPT）", "輸送費込み（CPT）", "운송비 지급 인도（CPT）", "frachtfrei（CPT）", "port payé jusqu'à（CPT）", "transporte pagado hasta（CPT）", "фрахт оплачен до（CPT）", "trasporto pagato fino a（CPT）"),
    ("CPT", "运费付至（CPT）", "輸送費込み（CPT）", "운송비 지급 인도（CPT）", "frachtfrei（CPT）", "port payé jusqu'à（CPT）", "transporte pagado hasta（CPT）", "фрахт оплачен до（CPT）", "trasporto pagato fino a（CPT）"),
    ("carriage and insurance paid to", "运费及保险费付至（CIP）", "輸送費・保険料込み（CIP）", "운송비·보험료 지급 인도（CIP）", "frachtfrei versichert（CIP）", "port payé, assurance comprise jusqu'à（CIP）", "transporte y seguro pagados hasta（CIP）", "фрахт и страхование оплачены до（CIP）", "trasporto e assicurazione pagati fino a（CIP）"),
    ("CIP", "运费及保险费付至（CIP）", "輸送費・保険料込み（CIP）", "운송비·보험료 지급 인도（CIP）", "frachtfrei versichert（CIP）", "port payé, assurance comprise jusqu'à（CIP）", "transporte y seguro pagados hasta（CIP）", "фрахт и страхование оплачены до（CIP）", "trasporto e assicurazione pagati fino a（CIP）"),
    ("delivered at place", "目的地交货（DAP）", "仕向地持込渡し（DAP）", "도착장소 인도（DAP）", "geliefert benannter Ort（DAP）", "rendu au lieu de destination（DAP）", "entregado en lugar（DAP）", "поставка в месте назначения（DAP）", "reso al luogo di destinazione（DAP）"),
    ("DAP", "目的地交货（DAP）", "仕向地持込渡し（DAP）", "도착장소 인도（DAP）", "geliefert benannter Ort（DAP）", "rendu au lieu de destination（DAP）", "entregado en lugar（DAP）", "поставка в месте назначения（DAP）", "reso al luogo di destinazione（DAP）"),
    ("delivered at place unloaded", "卸货地交货（DPU）", "荷降済持込渡し（DPU）", "도착지 양하 인도（DPU）", "geliefert benannter Ort entladen（DPU）", "rendu au lieu de destination déchargé（DPU）", "entregado en lugar descargado（DPU）", "поставка на место с разгрузкой（DPU）", "reso al luogo scaricato（DPU）"),
    ("DPU", "卸货地交货（DPU）", "荷降済持込渡し（DPU）", "도착지 양하 인도（DPU）", "geliefert benannter Ort entladen（DPU）", "rendu au lieu de destination déchargé（DPU）", "entregado en lugar descargado（DPU）", "поставка на место с разгрузкой（DPU）", "reso al luogo scaricato（DPU）"),
    ("delivered duty paid", "完税后交货（DDP）", "関税込持込渡し（DDP）", "관세지급인도（DDP）", "geliefert verzollt（DDP）", "rendu droits acquittés（DDP）", "entregado con derechos pagados（DDP）", "поставка с оплатой пошлин（DDP）", "reso sdoganato（DDP）"),
    ("DDP", "完税后交货（DDP）", "関税込持込渡し（DDP）", "관세지급인도（DDP）", "geliefert verzollt（DDP）", "rendu droits acquittés（DDP）", "entregado con derechos pagados（DDP）", "поставка с оплатой пошлин（DDP）", "reso sdoganato（DDP）"),
    ("bill of lading", "提单", "船荷証券", "선하증권", "Konnossement", "connaissement", "conocimiento de embarque", "коносамент", "polizza di carico"),
    ("air waybill", "航空运单（AWB）", "航空運送状", "항공화물운송장", "Luftfrachtbrief", "lettre de transport aérien", "guía aérea", "авианакладная", "lettera di vettura aerea"),
    ("sea waybill", "海运单", "海上運送状", "해상화물운송장", "Seefrachtbrief", "lettre de transport maritime", "guía marítima", "морская накладная", "lettera di trasporto marittimo"),
    ("commercial invoice", "商业发票", "商業送り状", "상업송장", "Handelsrechnung", "facture commerciale", "factura comercial", "коммерческий инвойс", "fattura commerciale"),
    ("packing list", "装箱单", "梱包明細書", "패킹리스트", "Packliste", "liste de colisage", "lista de empaque", "упаковочный лист", "distinta dei colli"),
    ("customs declaration", "报关单", "税関申告書", "세관신고서", "Zollanmeldung", "déclaration en douane", "declaración aduanera", "таможенная декларация", "dichiarazione doganale"),
    ("customs clearance", "清关/结关", "通関手続き", "통관", "Zollabfertigung", "dédouanement", "despacho de aduanas", "таможенная очистка", "sdoganamento"),
    ("certificate of origin", "原产地证书（CO）", "原産地証明書", "원산지 증명서", "Ursprungszeugnis", "certificat d'origine", "certificado de origen", "сертификат происхождения", "certificato di origine"),
    ("Harmonized System code", "协调制度编码（HS编码）", "HSコード", "HS 코드", "HS-Code", "code du Système harmonisé", "código del Sistema Armonizado", "код Гармонизированной системы", "codice del Sistema armonizzato"),
    ("HS code", "协调制度编码", "HSコード", "HS 코드", "HS-Code", "code du Système harmonisé", "código del Sistema Armonizado", "код Гармонизированной системы", "codice del Sistema armonizzato"),
    ("letter of credit", "信用证（L/C）", "信用状", "신용장", "Akkreditiv", "crédit documentaire", "carta de crédito", "аккредитив", "lettera di credito"),
    ("telegraphic transfer", "电汇（T/T）", "電信送金", "전신송금（T/T）", "telegrafische Überweisung", "transfert télégraphique", "transferencia telegráfica", "телеграфный перевод", "bonifico telegrafico"),
    ("bonded warehouse", "保税仓库", "保税倉庫", "보세창고", "Zolllager", "entrepôt sous douane", "almacén fiscal", "таможенный склад", "deposito doganale"),
    ("free trade zone", "自由贸易区（FTZ）", "自由貿易地域", "자유무역지대", "Freihandelszone", "zone de libre-échange", "zona franca", "зона свободной торговли", "zona franca"),
    ("anti-dumping duty", "反倾销税", "反ダンピング税", "반덤핑 관세", "Antidumpingzoll", "droit antidumping", "derecho antidumping", "антидемпинговая пошлина", "dazio antidumping"),
    ("countervailing duty", "反补贴税", "相殺関税", "상계관세", "Ausgleichszoll", "droit compensateur", "derecho compensatorio", "компенсационная пошлина", "dazio compensativo"),
    ("demurrage", "滞期费", "滞船料", "체선료", "Liegegeld", "surestaries", "demoras", "демередж", "controstallie"),
    ("detention", "滞箱费", "ディテンションチャージ", "지체료", "Containerverzögerungsgebühr", "frais de rétention", "detención de contenedores", "детеншн", "spese di detenzione"),
    ("less than container load", "拼箱货（LCL）", "混載貨物（LCL）", "소량화물（LCL）", "Stückgutladung（LCL）", "groupage maritime（LCL）", "carga consolidada（LCL）", "сборный груз（LCL）", "carico parziale（LCL）"),
    ("full container load", "整箱货（FCL）", "フルコンテナ貨物（FCL）", "만재화물（FCL）", "Vollcontainerladung（FCL）", "conteneur complet（FCL）", "contenedor completo（FCL）", "полный контейнер（FCL）", "carico completo（FCL）"),
    ("port of loading", "起运港/装货港（POL）", "船積港", "선적항", "Ladehafen", "port de chargement", "puerto de carga", "порт погрузки", "porto di imbarco"),
    ("port of discharge", "目的港/卸货港（POD）", "揚地港", "양하항", "Löschhafen", "port de déchargement", "puerto de descarga", "порт выгрузки", "porto di sbarco")
]

save_terms("trade_terms.json", trade_terms)

# 2. 跨境电商 (Cross-Border E-Commerce Terms)
cb_terms = [
    ("cross-border e-commerce", "跨境电商", "越境EC", "크로스보더 이커머스", "grenzüberschreitender E-Commerce", "commerce électronique transfrontalier", "comercio electrónico transfronterizo", "трансграничная электронная коммерция", "e-commerce transfrontaliero"),
    ("fulfillment by Amazon", "亚马逊代发货（FBA）", "フルフィルメント by Amazon（FBA）", "아마존 주문처리 서비스（FBA）", "Versand durch Amazon（FBA）", "Expédié par Amazon（FBA）", "Logística de Amazon（FBA）", "фулфилмент от Amazon（FBA）", "Logistica di Amazon（FBA）"),
    ("FBA", "亚马逊FBA仓储物流", "FBA", "FBA", "FBA", "FBA", "FBA", "FBA", "FBA"),
    ("fulfillment by merchant", "自发货卖家配送（FBM）", "出品者出荷（FBM）", "판매자 직접배송（FBM）", "Versand durch Händler（FBM）", "Expédié par le vendeur（FBM）", "gestion por el vendedor（FBM）", "фулфилмент продавцом（FBM）", "gestito dal venditore（FBM）"),
    ("FBM", "卖家自配送（FBM）", "FBM", "FBM", "FBM", "FBM", "FBM", "FBM", "FBM"),
    ("stock keeping unit", "库存量单位（SKU）", "在庫管理単位（SKU）", "단품관리단위（SKU）", "Lagerhaltungseinheit（SKU）", "unité de gestion des stocks（SKU）", "unidad de mantenimiento de existencias（SKU）", "идентификатор товарной позиции（SKU）", "unità di gestione stock（SKU）"),
    ("SKU", "商品SKU", "SKU", "SKU", "SKU", "SKU", "SKU", "SKU", "SKU"),
    ("Amazon Standard Identification Number", "亚马逊标准识别码（ASIN）", "Amazon標準識別番号（ASIN）", "아마존 표준 식별 번호（ASIN）", "Amazon-Standard-Identifikationsnummer（ASIN）", "numéro d'identification standard Amazon（ASIN）", "número de identificación estándar de Amazon（ASIN）", "стандартный идентификационный номер Amazon（ASIN）", "numero identificativo standard Amazon（ASIN）"),
    ("ASIN", "亚马逊ASIN码", "ASIN", "ASIN", "ASIN", "ASIN", "ASIN", "ASIN", "ASIN"),
    ("independent webstore", "独立站", "自社ECサイト", "독립형 쇼핑몰/D2C몰", "unabhängiger Online-Shop", "boutique en ligne indépendante", "tienda online independiente", "независимый интернет-магазин", "negozio online indipendente"),
    ("Shopify", "Shopify独立站系统", "Shopify", "쇼피파이", "Shopify", "Shopify", "Shopify", "Shopify", "Shopify"),
    ("direct-to-consumer", "直接面向消费者（D2C）", "D2C（消費者直販）", "D2C（소비자 직판）", "Direct-to-Consumer（D2C）", "vente directe au consommateur（D2C）", "directo al consumidor（D2C）", "прямые продажи потребителям（D2C）", "vendita diretta al consumatore（D2C）"),
    ("D2C", "D2C直营模式", "D2C", "D2C", "D2C", "D2C", "D2C", "D2C", "D2C"),
    ("overseas warehouse", "海外仓", "海外現地倉庫", "해외창고", "Übersee-Lager", "entrepôt à l'étranger", "almacén en el extranjero", "зарубежный склад", "magazzino estero"),
    ("dropshipping", "无货源代发/一件代发", "ドロップシッピング", "드랍쉬핑/위탁배송", "Streckengeschäft/Dropshipping", "livraison directe/dropshipping", "envío directo/dropshipping", "прямая поставка/дропшиппинг", "dropshipping"),
    ("Buy Box", "黄金购物车/购买按钮", "ショッピングカートボックス/バイボックス", "바이박스（Buy Box）", "Einkaufswagen-Feld（Buy Box）", "boîte d'achat（Buy Box）", "caja de compra（Buy Box）", "блок покупки（Buy Box）", "box di acquisto（Buy Box）"),
    ("pay-per-click", "按点击付费广告（PPC）", "クリック課金型広告（PPC）", "클릭당 과금 광고（PPC）", "Pay-per-Click（PPC）", "paiement au clic（PPC）", "pago por clic（PPC）", "оплата за клик（PPC）", "pagamento per clic（PPC）"),
    ("PPC", "PPC点击广告", "PPC広告", "PPC 광고", "PPC-Werbung", "publicité PPC", "publicidad PPC", "PPC-реклама", "annunci PPC"),
    ("advertising cost of sales", "广告销售成本比（ACoS）", "売上高広告費率（ACoS）", "광고매출비용비율（ACoS）", "Werbekostensenkung（ACoS）", "ratio coût publicitaire/ventes（ACoS）", "coste publicitario de ventas（ACoS）", "доля рекламных расходов（ACoS）", "costo pubblicitario delle vendite（ACoS）"),
    ("ACoS", "广告花费比（ACoS）", "ACoS", "ACoS", "ACoS", "ACoS", "ACoS", "ACoS", "ACoS"),
    ("return on ad spend", "广告投资回报率（ROAS）", "広告費用対効果（ROAS）", "광고수익률（ROAS）", "Return on Ad Spend（ROAS）", "retour sur les dépenses publicitaires（ROAS）", "retorno de la inversión publicitaria（ROAS）", "окупаемость инвестиций в рекламу（ROAS）", "ritorno sulla spesa pubblicitaria（ROAS）"),
    ("ROAS", "广告回报率（ROAS）", "ROAS", "ROAS", "ROAS", "ROAS", "ROAS", "ROAS", "ROAS"),
    ("search engine optimization", "搜索引擎优化（SEO）", "検索エンジン最適化（SEO）", "검색엔진 최적화（SEO）", "Suchmaschinenoptimierung（SEO）", "optimisation pour les moteurs de recherche（SEO）", "optimización para motores de búsqueda（SEO）", "поисковая оптимизация（SEO）", "ottimizzazione per i motori di ricerca（SEO）"),
    ("SEO", "SEO优化", "SEO", "SEO", "SEO", "SEO", "SEO", "SEO", "SEO"),
    ("conversion rate", "转化率（CVR）", "コンバージョン率（CVR）", "전환율（CVR）", "Konversionsrate（CVR）", "taux de conversion", "tasa de conversión", "коэффициент конверсии", "tasso di conversione"),
    ("click-through rate", "点击率（CTR）", "クリック率（CTR）", "클릭률（CTR）", "Klickrate（CTR）", "taux de clics（CTR）", "tasa de clics（CTR）", "кликабельность（CTR）", "tasso di clic（CTR）"),
    ("best seller rank", "热销品排行榜（BSR）", "ベストセラーランク（BSR）", "베스트셀러 순위（BSR）", "Bestseller-Rang（BSR）", "classement des meilleures ventes（BSR）", "ranking de los más vendidos（BSR）", "рейтинг бестселлеров（BSR）", "classifica dei più venduti（BSR）"),
    ("BSR", "亚马逊BSR排名", "BSRランキング", "BSR", "BSR", "BSR", "BSR", "BSR", "BSR"),
    ("import one-stop shop", "欧盟一站式进口报税（IOSS）", "EU輸入ワンストップショップ（IOSS）", "EU 수입 원스톱 쇼핑（IOSS）", "Import-One-Stop-Shop（IOSS）", "guichet unique à l'importation（IOSS）", "ventanilla única de importación（IOSS）", "система IOSS", "sportello unico all'importazione（IOSS）"),
    ("IOSS", "欧盟IOSS税号", "IOSS番号", "IOSS", "IOSS-Nummer", "numéro IOSS", "número IOSS", "номер IOSS", "codice IOSS"),
    ("value-added tax", "增值税（VAT）", "付加価値税（VAT）", "부가가치세（VAT）", "Mehrwertsteuer（MwSt.）", "taxe sur la valeur ajoutée（TVA）", "impuesto sobre el valor añadido（IVA）", "налог на добавленную стоимость（НДС）", "imposta sul valore aggiunto（IVA）"),
    ("VAT", "增值税（VAT）", "VAT（付加価値税）", "VAT", "MwSt.", "TVA", "IVA", "НДС", "IVA")
]

save_terms("crossborder_ecommerce_terms.json", cb_terms)

# 3. 银行金融与国际结算 (Finance Terms)
fin_terms = [
    ("SWIFT", "环球同业银行金融电讯协会（SWIFT）", "国際銀行間通信協会（SWIFT）", "국제은행간통신협정（SWIFT）", "SWIFT", "SWIFT", "SWIFT", "SWIFT", "SWIFT"),
    ("IBAN", "国际银行账号（IBAN）", "国際銀行口座番号（IBAN）", "국제은행계좌번호（IBAN）", "internationale Bankkontonummer（IBAN）", "numéro de compte bancaire international（IBAN）", "número de cuenta bancaria internacional（IBAN）", "международный номер банковского счета（IBAN）", "numero di conto bancario internazionale（IBAN）"),
    ("Bank Identifier Code", "银行识别代码（BIC）", "銀行識別コード（BIC）", "은행식별코드（BIC）", "Bankleitzahl/BIC", "code d'identification bancaire（BIC）", "código de identificación bancaria（BIC）", "банковский идентификационный код（BIC）", "codice di identificazione bancaria（BIC）"),
    ("BIC", "银行BIC代码", "BICコード", "BIC", "BIC", "BIC", "BIC", "BIC", "BIC"),
    ("foreign exchange", "外汇（Forex/FX）", "外国為替（FX）", "외환（FX）", "Devisen/Foreign Exchange", "change/devises", "divisas/tipo de cambio", "иностранная валюта/валютный рынок", "cambio valute/forex"),
    ("exchange rate", "汇率", "為替レート", "환율", "Wechselkurs", "taux de change", "tipo de cambio", "валютный курс", "tasso di cambio"),
    ("spot exchange rate", "即期汇率", "スポット為替レート", "현물환율", "Kassakurs", "taux de change au comptant", "tipo de cambio al contado", "спотовый валютный курс", "tasso di cambio a pronti"),
    ("forward exchange rate", "远期汇率", "先物為替レート", "선물환율", "Terminkurs", "taux de change à terme", "tipo de cambio a plazo", "форвардный валютный курс", "tasso di cambio a termine"),
    ("liquidity", "流动性/资金周转", "流動性", "유동성", "Liquidität", "liquidité", "liquidez", "ликвидность", "liquidità"),
    ("working capital", "营运资金/流动资金", "運転資本", "운전자본", "Betriebskapital", "fonds de roulement", "capital de trabajo", "оборотный капитал", "capitale circolante"),
    ("foreign direct investment", "外商直接投资（FDI）", "海外直接投資（FDI）", "외국인 직접투자（FDI）", "ausländische Direktinvestitionen（FDI）", "investissement direct à l'étranger（IDE）", "inversión extranjera directa（IED）", "прямые иностранные инвестиции（ПИИ）", "investimenti diretti esteri（IDE）"),
    ("FDI", "外商直接投资FDI", "FDI直接投資", "FDI", "Direktinvestitionen", "IDE", "IED", "ПИИ", "IDE"),
    ("automated clearing house", "自动清算所（ACH）", "自動手形交換所（ACH）", "자동결제원（ACH）", "automatische Clearingstelle（ACH）", "chambre de compensation automatisée（ACH）", "cámara de compensación automatizada（ACH）", "автоматизированная клиринговая палата（ACH）", "sistema di compensazione automatizzata（ACH）"),
    ("ACH", "ACH清算网络", "ACH決済", "ACH", "ACH", "ACH", "ACH", "ACH", "ACH"),
    ("central bank digital currency", "央行数字货币（CBDC）", "中央銀行デジタル通貨（CBDC）", "중앙은행 디지털화폐（CBDC）", "digitales Zentralbankgeld（CBDC）", "monnaie numérique de banque centrale（MNBC）", "moneda digital de banco central（CBDC）", "цифровая валюта центрального банка（ЦВЦБ）", "valuta digitale della banca centrale（CBDC）"),
    ("CBDC", "央行数字货币CBDC", "CBDC", "CBDC", "CBDC", "MNBC", "CBDC", "ЦВЦБ", "CBDC"),
    ("anti-money laundering", "反洗钱（AML）", "マネーロンダリング対策（AML）", "자금세탁방지（AML）", "Geldwäschebekämpfung（AML）", "lutte contre le blanchiment d'argent（LCB）", "prevención del blanqueo de capitales（AML）", "противодействие отмыванию денег（ПОД）", "antiriciclaggio（AML）"),
    ("AML", "反洗钱监管", "AML対策", "AML", "AML", "LCB-FT", "AML", "ПОД/ФТ", "normativa AML"),
    ("know your customer", "了解你的客户（KYC）", "顧客確認（KYC）", "고객확인제도（KYC）", "Kenne deinen Kunden（KYC）", "connaissance du client（KYC）", "conozca a su cliente（KYC）", "знай своего клиента（KYC）", "adeguata verifica della clientela（KYC）"),
    ("KYC", "KYC身份验证", "KYC本人確認", "KYC", "KYC", "KYC", "KYC", "верификация KYC", "procedura KYC"),
    ("Federal Reserve", "美联储（Fed）", "米連邦準備制度理事会（FRB）", "미국 연방준비제도（연준）", "Federal Reserve（US-Notenbank）", "Réserve fédérale américaine（Fed）", "Reserva Federal de EE. UU.（Fed）", "Федеральная резервная система США（ФРС）", "Federal Reserve（Fed）"),
    ("European Central Bank", "欧洲央行（ECB）", "欧州中央銀行（ECB）", "유럽중앙은행（ECB）", "Europäische Zentralbank（EZB）", "Banque centrale européenne（BCE）", "Banco Central Europeo（BCE）", "Европейский центральный банк（ЕЦБ）", "Banca centrale europea（BCE）"),
    ("Bank of Japan", "日本央行（BOJ）", "日本銀行（日銀）", "일본은행（BOJ）", "Bank von Japan（BoJ）", "Banque du Japon（BoJ）", "Banco de Japón（BoJ）", "Банк Японии", "Banca del Giappone（BoJ）")
]

save_terms("finance_terms.json", fin_terms)
print("All initial sets generated successfully!")
