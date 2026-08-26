#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full 9-Language Specialized Terminology Expander (200+ terms per catalog)."""

from term_catalog_utils import merge_catalog


def merge_terms(filename, new_entries):
    total = merge_catalog(filename, new_entries)
    print(f"✓ {filename}: total {total} terms")

# ==============================================================================
# 1. 跨境电商 (crossborder_ecommerce_terms.json) -> 200+
# ==============================================================================
cb_additions = [
    ("fulfillment by Amazon", "亚马逊代发货（FBA）", "フルフィルメント by Amazon（FBA）", "아마존 주문처리 서비스（FBA）", "Versand durch Amazon（FBA）", "Expédié par Amazon（FBA）", "Logística de Amazon（FBA）", "фулфилмент от Amazon（FBA）", "Logistica di Amazon（FBA）"),
    ("FBA", "亚马逊FBA仓储物流", "FBA", "FBA", "FBA", "FBA", "FBA", "FBA", "FBA"),
    ("fulfillment by merchant", "自发货卖家配送（FBM）", "出品者出荷（FBM）", "판매자 직접배송（FBM）", "Versand durch Händler（FBM）", "Expédié par le vendeur（FBM）", "gestion por el vendedor（FBM）", "фулфилмент продавцом（FBM）", "gestito dal venditore（FBM）"),
    ("FBM", "卖家自配送（FBM）", "FBM", "FBM", "FBM", "FBM", "FBM", "FBM", "FBM"),
    ("stock keeping unit", "库存量单位（SKU）", "在庫管理単位（SKU）", "단품관리단위（SKU）", "Lagerhaltungseinheit（SKU）", "unité de gestion des stocks（SKU）", "unidad de mantenimiento de existencias（SKU）", "идентификатор товарной позиции（SKU）", "unità di gestione stock（SKU）"),
    ("SKU", "商品SKU", "SKU", "SKU", "SKU", "SKU", "SKU", "SKU", "SKU"),
    ("Amazon Standard Identification Number", "亚马逊标准识别码（ASIN）", "Amazon標準識別番号（ASIN）", "아마존 표준 식별 번호（ASIN）", "Amazon-Standard-Identifikationsnummer（ASIN）", "numéro d'identification standard Amazon（ASIN）", "número de identificación estándar de Amazon（ASIN）", "стандартный идентификационный номер Amazon（ASIN）", "numero identificativo standard Amazon（ASIN）"),
    ("ASIN", "亚马逊ASIN码", "ASIN", "ASIN", "ASIN", "ASIN", "ASIN", "ASIN", "ASIN"),
    ("independent webstore", "独立站", "自社ECサイト", "독립형 쇼핑몰/D2C몰", "unabhängiger Online-Shop", "boutique en ligne indépendante", "tienda online independiente", "независимый интернет-магазин", "negozio online indipendente"),
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
    ("conversion rate", "转化率（CVR）", "コンバージョン率（CVR）", "전환율（CVR）", "Konversionsrate（CVR）", "taux de conversion", "tasa de conversión", "коэффициент конверсии", "tasso di conversione"),
    ("click-through rate", "点击率（CTR）", "クリック率（CTR）", "클릭률（CTR）", "Klickrate（CTR）", "taux de clics（CTR）", "tasa de clics（CTR）", "кликабельность（CTR）", "tasso di clic（CTR）"),
    ("best seller rank", "热销品排行榜（BSR）", "ベストセラーランク（BSR）", "베스트셀러 순위（BSR）", "Bestseller-Rang（BSR）", "classement des meilleures ventes（BSR）", "ranking de los más vendidos（BSR）", "рейтинг бестселлеров（BSR）", "classifica dei più venduti（BSR）"),
    ("BSR", "亚马逊BSR排名", "BSRランキング", "BSR", "BSR", "BSR", "BSR", "BSR", "BSR"),
    ("import one-stop shop", "欧盟一站式进口报税（IOSS）", "EU輸入ワンストップショップ（IOSS）", "EU 수입 원스톱 쇼핑（IOSS）", "Import-One-Stop-Shop（IOSS）", "guichet unique à l'importation（IOSS）", "ventanilla única de importación（IOSS）", "система IOSS", "sportello unico all'importazione（IOSS）"),
    ("IOSS", "欧盟IOSS税号", "IOSS番号", "IOSS", "IOSS-Nummer", "numéro IOSS", "número IOSS", "номер IOSS", "codice IOSS"),
    ("value-added tax", "增值税（VAT）", "付加価値税（VAT）", "부가가치세（VAT）", "Mehrwertsteuer（MwSt.）", "taxe sur la valeur ajoutée（TVA）", "impuesto sobre el valor añadido（IVA）", "налог на добавленную стоимость（НДС）", "imposta sul valore aggiunto（IVA）"),
    ("VAT", "增值税（VAT）", "VAT（付加価値税）", "VAT", "MwSt.", "TVA", "IVA", "НДС", "IVA"),
    ("order fulfillment", "订单履约", "注文処理/フルフィルメント", "주문이행/풀필먼트", "Auftragsabwicklung", "exécution des commandes", "cumplimiento de pedidos", "обработка и выполнение заказов", "evasione degli ordini"),
    ("refund", "退款", "返金/リファンド", "환불", "Rückerstattung", "remboursement", "reembolso", "возврат денежных средств", "rimborso"),
    ("chargeback", "拒付/退单", "チャージバック", "결제취소/차지백", "Rückbuchung/Chargeback", "rétrofacturation", "contracargo", "чарджбэк/возвратный платеж", "storno di addebito"),
    ("cash on delivery", "货到付款（COD）", "代金引換（COD）", "착불/대금상환（COD）", "Nachnahme（COD）", "paiement à la livraison（COD）", "pago contra reembolso（COD）", "наложенный платеж（COD）", "pagamento alla consegna（COD）"),
    ("COD", "货到付款（COD）", "COD（代引き）", "COD", "Nachnahme", "paiement COD", "pago COD", "оплата COD", "servizio COD"),
    ("A+ Content", "A+高级图文详情页", "A+コンテンツ/商品紹介コンテンツ", "A+ 프리미엄 상세페이지", "Erweiterte Markeninhalte（A+ Content）", "contenu de marque amélioré（A+）", "contenido A+", "A+ контент", "contenuto A+"),
    ("cross-docking", "越库配送/直通转运", "クロスドッキング", "크로스도킹", "Kreuzverkupplung/Cross-Docking", "cross-docking", "cruce de andén/cross-docking", "кросс-докинг", "cross-docking"),
    ("return merchandise authorization", "退货授权（RMA）", "返品確認番号（RMA）", "반품승인（RMA）", "Rücksendenummer（RMA）", "autorisation de retour de marchandise（RMA）", "autorización de devolución de mercancía（RMA）", "разрешение на возврат товара（RMA）", "autorizzazione al reso di merce（RMA）"),
    ("RMA", "RMA退货授权", "RMA番号", "RMA", "RMA", "RMA", "RMA", "RMA", "RMA"),
    ("minimum order quantity", "最小起订量（MOQ）", "最小発注数量（MOQ）", "최소주문수량（MOQ）", "Mindestbestellmenge（MOQ）", "quantité minimale de commande（MOQ）", "cantidad mínima de pedido（MOQ）", "минимальный объем заказа（MOQ）", "quantità minima d'ordine（MOQ）"),
    ("MOQ", "起订量MOQ", "MOQ", "MOQ", "Mindestmenge", "quantité MOQ", "pedido MOQ", "MOQ", "quantità MOQ"),
    ("original equipment manufacturer", "原始设备制造商/贴牌代工（OEM）", "相手先商標製品製造業者（OEM）", "주문자 상표 부착 생산（OEM）", "Originalgerätehersteller（OEM）", "fabricant d'équipement d'origine（OEM）", "fabricante de equipo original（OEM）", "производитель комплектного оборудования（OEM）", "produttore di apparecchiature originali（OEM）"),
    ("OEM", "OEM代工", "OEM生産", "OEM", "OEM", "OEM", "OEM", "OEM", "OEM"),
    ("original design manufacturer", "原始设计制造商/设计代工（ODM）", "相手先ブランド設計製造業者（ODM）", "제조자 개발생산（ODM）", "Originaldesignhersteller（ODM）", "concepteur et fabricant d'origine（ODM）", "fabricante de diseño original（ODM）", "производитель оригинального дизайна（ODM）", "produttore di design originale（ODM）"),
    ("ODM", "ODM设计代工", "ODM生産", "ODM", "ODM", "ODM", "ODM", "ODM", "ODM"),
    ("private label", "自有品牌/白标定制", "プライベートブランド（PB）", "자체 상표（PB）", "Eigenmarke/Private Label", "marque de distributeur", "marca blanca/marca privada", "собственная торговая марка（СТМ）", "marchio del distributore"),
    ("third-party logistics", "第三方物流（3PL）", "サードパーティロジスティクス（3PL）", "제3자 물류（3PL）", "Drittanbieterlogistik（3PL）", "logistique tierce partie（3PL）", "logística de terceros（3PL）", "логистика стороннего оператора（3PL）", "logistica conto terzi（3PL）"),
    ("3PL", "第三方物流3PL", "3PL業者", "3PL", "3PL-Dienstleister", "prestataire 3PL", "operador 3PL", "3PL-провайдер", "operatore 3PL"),
    ("warehouse management system", "仓库管理系统（WMS）", "倉庫管理システム（WMS）", "창고관리시스템（WMS）", "Lagerverwaltungssystem（WMS）", "système de gestion d'entrepôt（WMS）", "sistema de gestión de almacenes（WMS）", "система управления складом（WMS）", "sistema di gestione del magazzino（WMS）"),
    ("WMS", "WMS仓库系统", "WMS", "WMS", "WMS", "WMS", "WMS", "WMS", "WMS"),
    ("order management system", "订单管理系统（OMS）", "注文管理システム（OMS）", "주문관리시스템（OMS）", "Auftragsabwicklungssystem（OMS）", "système de gestion des commandes（OMS）", "sistema de gestión de pedidos（OMS）", "система управления заказами（OMS）", "sistema di gestione degli ordini（OMS）"),
    ("OMS", "OMS订单系统", "OMS", "OMS", "OMS", "OMS", "OMS", "OMS", "OMS")
]

merge_terms("crossborder_ecommerce_terms.json", cb_additions)

# ==============================================================================
# 2. 金融 (finance_terms.json) -> 200+
# ==============================================================================
fin_additions = [
    ("inflation", "通货膨胀", "インフレーション", "인플레이션", "Inflation", "inflation", "inflación", "инфляция", "inflazione"),
    ("deflation", "通货紧缩", "デフレーション", "디플레이션", "Deflation", "déflation", "deflación", "дефляция", "deflazione"),
    ("quantitative easing", "量化宽松", "量的金融緩和", "양적완화", "quantitative Lockerung", "assouplissement quantitatif", "flexibilización cuantitativa", "количественное смягчение", "allentamento quantitativo"),
    ("quantitative tightening", "量化紧缩", "量的引き締め", "양적긴축", "quantitative Straffung", "resserrement quantitatif", "ajuste cuantitativo", "количественное ужесточение", "stretta quantitativa"),
    ("foreign exchange", "外汇（Forex/FX）", "外国為替（FX）", "외환（FX）", "Devisen", "change/devises", "divisas", "иностранная валюта", "valuta estera"),
    ("forex", "外汇市场", "外国為替取引", "외환시장", "Devisenmarkt", "marché des changes", "mercado de divisas", "валютный рынок Форекс", "mercato valutario"),
    ("exchange rate", "汇率", "為替レート", "환율", "Wechselkurs", "taux de change", "tipo de cambio", "валютный курс", "tasso di cambio"),
    ("liquidity", "流动性", "流動性", "유동성", "Liquidität", "liquidité", "liquidez", "ликвидность", "liquidità"),
    ("working capital", "营运资金", "運転資本", "운전자본", "Betriebskapital", "fonds de roulement", "capital de trabajo", "оборотный капитал", "capitale circolante"),
    ("yield curve", "收益率曲线", "利回り曲線", "수익률 곡선", "Zinsstrukturkurve", "courbe des rendements", "curva de rendimiento", "кривая доходности", "curva dei rendimenti"),
    ("interest rate swap", "利率互换（IRS）", "金利スワップ（IRS）", "금리스왑（IRS）", "Zinsswap", "swap de taux d'intérêt", "permuta financiera de tipos de interés", "процентный своп", "swap su tassi di interesse"),
    ("credit default swap", "信用违约互换（CDS）", "信用デフォルト・スワップ（CDS）", "신용부도스왑（CDS）", "Kreditausfallswap（CDS）", "dérivé de crédit（CDS）", "permuta de incumplimiento crediticio（CDS）", "кредитный дефолтный своп（CDS）", "credit default swap（CDS）"),
    ("commercial paper", "商业票据（CP）", "コマーシャル・ペーパー（CP）", "기업어음（CP）", "Commercial Paper", "billet de trésorerie", "papel comercial", "коммерческие бумаги", "carta commerciale"),
    ("treasury bill", "短期国债（T-Bill）", "短期国債（T-Bill）", "미국 단기재정증권（T-Bill）", "Schatzanweisung（T-Bill）", "bon du Trésor à court terme", "letra del Tesoro", "казначейский вексель США", "buono del tesoro a breve termine"),
    ("treasury bond", "中长期国债（T-Bond）", "長期国債（T-Bond）", "미국 장기국채（T-Bond）", "Staatsanleihe（T-Bond）", "obligation du Trésor à long terme", "bono del Tesoro", "казначейская облигация США", "buono del tesoro poliennale"),
    ("discounted cash flow", "现金流折现模型（DCF）", "割引キャッシュフロー法（DCF）", "현금흐름할인법（DCF）", "Discounted-Cashflow-Verfahren", "flux de trésorerie actualisés", "flujo de caja descontado", "дисконтированный денежный поток", "flussi di cassa scontati"),
    ("internal rate of return", "内部收益率（IRR）", "内部収益率（IRR）", "내부수익률（IRR）", "interner Zinsfuß", "taux de rentabilité interne", "tasa interna de retorno", "внутренняя норма доходности", "tasso interno di rendimento"),
    ("net present value", "净现值（NPV）", "正味現在価値（NPV）", "순현재가치（NPV）", "Kapitalwert/Nettobarwert", "valeur actuelle nette", "valor actual neto", "чистая приведенная стоимость", "valore attuale netto"),
    ("amortization", "摊销/分期偿还", "減価償却/分割償還", "상각/분할상환", "Amortisation/Tilgung", "amortissement", "amortización", "амортизация", "ammortamento"),
    ("collateral", "抵押品/担保物", "担保/抵当物件", "담보물", "Kreditsicherheit", "garantie/collatéral", "colateral/garantía", "залоговое обеспечение", "garanzia collaterale"),
    ("securitization", "资产证券化", "資産証券化", "자산유동화/증권화", "Verbriefung", "titrisation", "titulización de activos", "секьюритизация активов", "cartolarizzazione"),
    ("special purpose vehicle", "特殊目的实体（SPV）", "特別目的会社（SPV）", "특수목적법인（SPV）", "Zweckgesellschaft（SPV）", "véhicule de titrisation（SPV）", "entidad de propósito especial（SPV）", "специальное юридическое лицо（SPV）", "società veicolo（SPV）"),
    ("Federal Reserve", "美联储（Fed）", "米連邦準備制度理事会（FRB）", "미국 연방준비제도（연준）", "Federal Reserve", "Réserve fédérale américaine（Fed）", "Reserva Federal（Fed）", "Федеральная резервная система США（ФРС）", "Federal Reserve（Fed）"),
    ("European Central Bank", "欧洲央行（ECB）", "欧州中央銀行（ECB）", "유럽중앙은행（ECB）", "Europäische Zentralbank（EZB）", "Banque centrale européenne（BCE）", "Banco Central Europeo（BCE）", "Европейский центральный банк（ЕЦБ）", "Banca centrale europea（BCE）"),
    ("Bank of Japan", "日本央行（BOJ）", "日本銀行（日銀）", "일본은행（BOJ）", "Bank von Japan（BoJ）", "Banque du Japon（BoJ）", "Banco de Japón（BoJ）", "Банк Японии", "Banca del Giappone（BoJ）"),
    ("prime rate", "最优惠贷款利率", "プライムレート", "우대금리", "Leitzins/Prime Rate", "taux préférentiel", "tipo de interés preferencial", "базовая ставка", "tasso primario"),
    ("non-performing loan", "不良贷款（NPL）", "不良債権（NPL）", "부실채권（NPL）", "notleidender Kredit（NPL）", "créance douteuse（NPL）", "préstamo dudoso（NPL）", "неработающий кредит（NPL）", "credito deteriorato（NPL）"),
    ("capital adequacy ratio", "资本充足率（CAR）", "自己資本比率（CAR）", "자기자본비율（CAR）", "Eigenkapitalquote", "ratio de solvabilité", "coeficiente de solvencia bancaria", "коэффициент достаточности капитала", "indice di adeguatezza patrimoniale"),
    ("Basel III", "巴塞尔协议III", "バーゼルIII規制", "바젤 III 협약", "Basel III", "Bâle III", "Basilea III", "Базель III", "Basilea III"),
    ("sovereign wealth fund", "主权财富基金（SWF）", "政府系投資ファンド（SWF）", "국부펀드（SWF）", "Staatsfonds（SWF）", "fonds souverain", "fondo soberano de inversión", "суверенный фонд благосостояния", "fondo sovrano")
]

merge_terms("finance_terms.json", fin_additions)

# ==============================================================================
# 3. 硬件制造与电子工程 (hardware_terms.json) -> 200+
# ==============================================================================
hw_additions = [
    ("printed circuit board", "印制电路板", "プリント基板", "인쇄회로기판（PCB）", "Leiterplatte（PCB）", "circuit imprimé（PCB）", "placa de circuito impreso（PCB）", "печатная плата（PCB）", "circuito stampato（PCB）"),
    ("PCB", "PCB电路板", "PCB基板", "PCB", "PCB", "PCB", "PCB", "печатная плата", "scheda PCB"),
    ("water cooling", "水冷", "水冷システム", "수랭식 냉각", "Wasserkühlung", "refroidissement liquide", "refrigeración líquida", "водяное охлаждение", "raffreddamento a liquido"),
    ("surface-mount technology", "表面贴装技术（SMT）", "表面実装技術（SMT）", "표면실장기술（SMT）", "Oberflächenmontagetechnik（SMT）", "technologie de montage en surface（CMS）", "tecnología de montaje superficial（SMT）", "технология поверхностного монтажа（ТПМ/SMT）", "tecnologia a montaggio superficiale（SMT）"),
    ("SMT", "SMT贴片加工", "SMT実装", "SMT", "SMT", "CMS", "SMT", "SMT-монтаж", "montaggio SMT"),
    ("semiconductor fabrication", "半导体晶圆制造", "半導体製造（ファブ）", "반도체 팹 제조", "Halbleiterfertigung", "fabrication de semi-conducteurs", "fabricación de semiconductores", "производство полупроводников", "fabbricazione di semiconduttori"),
    ("wafer", "晶圆/硅片", "ウェハー/半導体素子", "웨이퍼", "Silizium-Wafer", "plaquette de silicium/wafer", "oblea de silicio/wafer", "кремниевая пластина", "wafer di silicio"),
    ("integrated circuit", "集成电路（IC）", "集積回路（IC）", "집적회로（IC）", "integrierter Schaltkreis（IC）", "circuit intégré（CI）", "circuito integrado（CI）", "интегральная схема（ИС）", "circuito integrato（CI）"),
    ("system on a chip", "系统级芯片（SoC）", "システム・オン・チップ（SoC）", "단일 칩 시스템（SoC）", "System-on-a-Chip（SoC）", "système sur puce（SoC）", "sistema en un chip（SoC）", "система на кристалле（СнК/SoC）", "sistema su chip（SoC）"),
    ("SoC", "SoC芯片", "SoC", "SoC", "SoC", "SoC", "SoC", "чип SoC", "SoC"),
    ("microcontroller unit", "微控制器/单片机（MCU）", "マイクロコントローラ（MCU）", "마이크로컨트롤러（MCU）", "Mikrocontroller（MCU）", "microcontrôleur（MCU）", "microcontrolador（MCU）", "микроконтроллер（МК/MCU）", "microcontrollore（MCU）"),
    ("MCU", "MCU单片机", "MCU", "MCU", "MCU", "MCU", "MCU", "микроконтроллер", "MCU"),
    ("field-programmable gate array", "现场可编程门阵列（FPGA）", "FPGA（フィールドプログラマブルゲートアレイ）", "FPGA（프로그래머블 반도체）", "FPGA", "FPGA", "matriz de puertas lógicas programable en campo（FPGA）", "программируемая пользователем вентильная матрица（ПЛИС/FPGA）", "FPGA"),
    ("FPGA", "FPGA可编程芯片", "FPGA", "FPGA", "FPGA", "FPGA", "FPGA", "ПЛИС/FPGA", "FPGA"),
    ("heatsink", "散热片/散热器", "ヒートシンク/放熱器", "방열판/히트싱크", "Kühlkörper", "dissipateur thermique", "disipador térmico", "радиатор охлаждения", "dissipatore di calore"),
    ("thermal interface material", "导热界面材料（TIM）", "熱伝導材料（TIM）", "열전도 계면물질（TIM）", "Wärmeleitmaterial（TIM）", "matériau d'interface thermique（TIM）", "material de interfaz térmica（TIM）", "термоинтерфейсный материал（TIM）", "materiale di interfaccia termica（TIM）")
]

merge_terms("hardware_terms.json", hw_additions)

# ==============================================================================
# 4. 高分子材料 (materials_terms.json) -> 200+
# ==============================================================================
mat_additions = [
    ("polypropylene", "聚丙烯（PP）", "ポリプロピレン（PP）", "폴리프로필렌（PP）", "Polypropylen（PP）", "polypropylène（PP）", "polipropileno（PP）", "полипропилен（ПП）", "polipropilene（PP）"),
    ("polyethylene", "聚乙烯（PE）", "ポリエチレン（PE）", "폴리에틸렌（PE）", "Polyethylen（PE）", "polyéthylène（PE）", "polietileno（PE）", "полиэтилен（ПЭ）", "polietilene（PE）"),
    ("polyethylene terephthalate", "聚对苯二甲酸乙二醇酯（PET）", "ポリエチレンテレフタラート（PET）", "폴리에틸렌 테레프탈레이트（PET）", "Polyethylenterephthalat（PET）", "polyéthylène téréphtalate（PET）", "tereftalato de polietileno（PET）", "полиэтилентерефталат（ПЭТ）", "polietilene tereftalato（PET）"),
    ("polyvinyl chloride", "聚氯乙烯（PVC）", "ポリ塩化ビニル（PVC）", "폴리염화비닐（PVC）", "Polyvinylchlorid（PVC）", "polychlorure de vinyle（PVC）", "policloruro de vinilo（PVC）", "поливинилхлорид（ПВХ）", "polivinilcloruro（PVC）"),
    ("acrylonitrile butadiene styrene", "ABS工程塑料", "ABS樹脂", "ABS 수지", "Acrylnitril-Butadien-Styrol（ABS）", "acrylonitrile butadiène styrène（ABS）", "acrilonitrilo butadieno estireno（ABS）", "АБС-пластик", "acrilonitrile-butadiene-stirene（ABS）"),
    ("polycarbonate", "聚碳酸酯（PC）", "ポリカーボネート（PC）", "폴리카보네이트（PC）", "Polycarbonat（PC）", "polycarbonate（PC）", "policarbonato（PC）", "поликарбонат（ПК）", "policarbonato（PC）"),
    ("polystyrene", "聚苯乙烯（PS）", "ポリスチレン（PS）", "폴리스티렌（PS）", "Polystyrol（PS）", "polystyrène（PS）", "poliestireno（PS）", "полистирол（ПС）", "polistirene（PS）"),
    ("polyamide", "聚酰胺/尼龙（PA）", "ポリアミド/ナイロン（PA）", "폴리아미드/나일론（PA）", "Polyamid/Nylon（PA）", "polyamide/nylon（PA）", "poliamida/nailon（PA）", "полиамид/нейлон（ПА）", "poliammide/nylon（PA）"),
    ("polyurethane", "聚氨酯（PU）", "ポリウレタン（PU）", "폴리우레탄（PU）", "Polyurethan（PU）", "polyuréthane（PU）", "poliuretano（PU）", "полиуретан（ПУ）", "poliuretano（PU）"),
    ("polylactic acid", "聚乳酸可降解塑料（PLA）", "ポリ乳酸（PLA）", "폴리락트산/생분해성 수지（PLA）", "Polymilchsäure（PLA）", "acide polylactique（PLA）", "ácido poliláctico（PLA）", "полилактид（ПЛА）", "acido polilattico（PLA）"),
    ("injection molding", "注塑成型", "射出成形", "사출성형", "Spritzgießen", "moulage par injection", "moldeo por inyección", "литье под давлением", "stampaggio a iniezione")
]

merge_terms("materials_terms.json", mat_additions)

# ==============================================================================
# 5. 区块链与数字资产 (blockchain_terms.json) -> 200+
# ==============================================================================
bc_additions = [
    ("wallet", "钱包", "ウォレット", "지갑", "Wallet", "portefeuille", "billetera", "кошелек", "portafoglio"),
    ("blockchain", "区块链", "ブロックチェーン", "블록체인", "Blockchain", "blockchain", "cadena de bloques", "блокчейн", "blockchain"),
    ("cryptocurrency", "加密货币", "暗号資産/仮想通貨", "암호화폐", "Kryptowährung", "cryptomonnaie", "criptomoneda", "криптовалюта", "criptovaluta"),
    ("Bitcoin", "比特币", "ビットコイン", "비트코인", "Bitcoin", "Bitcoin", "Bitcoin", "Биткоин", "Bitcoin"),
    ("Ethereum", "以太坊", "イーサリアム", "이더리움", "Ethereum", "Ethereum", "Ethereum", "Эфириум", "Ethereum"),
    ("smart contract", "智能合约", "スマートコントラクト", "스마트 계약", "Smart Contract", "contrat intelligent", "contrato inteligente", "смарт-контракт", "smart contract"),
    ("decentralized finance", "去中心化金融（DeFi）", "分散型金融（DeFi）", "탈중앙화 금융（DeFi）", "dezentrale Finanzen（DeFi）", "finance décentralisée（DeFi）", "finanzas descentralizadas（DeFi）", "децентрализованные финансы（DeFi）", "finanza decentralizzata（DeFi）"),
    ("non-fungible token", "非同质化代币（NFT）", "非代替性トークン（NFT）", "대체불가토큰（NFT）", "Non-Fungible Token（NFT）", "jeton non fongible（NFT）", "token no fungible（NFT）", "невзаимозаменяемый токен（NFT）", "token non fungibile（NFT）"),
    ("proof of work", "工作量证明（PoW）", "プルーフ・オブ・ワーク（PoW）", "작업증명（PoW）", "Proof of Work（PoW）", "preuve de travail（PoW）", "prueba de trabajo（PoW）", "доказательство выполнения работы（PoW）", "proof of work（PoW）"),
    ("proof of stake", "权益证明（PoS）", "プルーフ・オブ・ステーク（PoS）", "지분증명（PoS）", "Proof of Stake（PoS）", "preuve d'enjeu（PoS）", "prueba de participación（PoS）", "доказательство доли владения（PoS）", "proof of stake（PoS）"),
    ("hash rate", "算力/哈希率", "ハッシュレート", "해시레이트/연산력", "Hashrate", "taux de hachage", "tasa de hash", "хешрейт", "hash rate")
]

merge_terms("blockchain_terms.json", bc_additions)

# ==============================================================================
# 6. 证券与股票市场 (stocks_terms.json) -> 200+
# ==============================================================================
st_additions = [
    ("initial public offering", "首次公开募股（IPO）", "新規株式公開（IPO）", "기업공개（IPO）", "Börsengang（IPO）", "introduction en bourse（IPO）", "oferta pública inicial（OPI）", "первичное публичное размещение（IPO）", "offerta pubblica iniziale（IPO）"),
    ("IPO", "IPO上市", "IPO", "IPO", "IPO", "IPO", "IPO", "IPO", "IPO"),
    ("market capitalization", "市值/股票总市值", "時価総額", "시가총액", "Marktkapitalisierung", "capitalisation boursière", "capitalización de mercado", "рыночная капитализация", "capitalizzazione di mercato"),
    ("price-to-earnings ratio", "市盈率（P/E）", "株価収益率（PER）", "주가수익비율（PER）", "Kurs-Gewinn-Verhältnis（KGV）", "ratio cours/bénéfice（PER）", "relación precio-beneficio（PER）", "коэффициент цена/прибыль（P/E）", "rapporto prezzo/utili（P/E）"),
    ("P/E ratio", "市盈率", "PER", "PER", "KGV", "PER", "PER", "мультипликатор P/E", "rapporto P/U"),
    ("dividend yield", "股息率", "配当利回り", "배당수익률", "Dividendenrendite", "rendement du dividende", "rendimiento por dividendo", "дивидендная доходность", "rendimento del dividendo"),
    ("short selling", "卖空/融券做空", "空売り/ショートセリング", "공매도", "Leerverkauf", "vente à découvert", "venta en corto", "короткая продажа/шорт", "vendita allo scoperto"),
    ("bull market", "牛市/多头市场", "強気相場/ブルマーケット", "상승장/강세장", "Bullenmarkt/Hausse", "marché haussier", "mercado alcista", "бычий рынок", "mercato rialzista"),
    ("bear market", "熊市/空头市场", "弱気相場/ベアマーケット", "하락장/약세장", "Bärenmarkt/Baisse", "marché baissier", "mercado bajista", "медвежий рынок", "mercato ribassista"),
    ("securities exchange", "证券交易所", "証券取引所", "증권거래소", "Wertpapierbörse", "bourse des valeurs", "bolsa de valores", "фондовая биржа", "borsa valori")
]

merge_terms("stocks_terms.json", st_additions)

# ==============================================================================
# 7. 前沿科技与AI/云计算 (tech_terms.json) -> 200+
# ==============================================================================
tech_additions = [
    ("artificial intelligence", "人工智能（AI）", "人工知能（AI）", "인공지능（AI）", "künstliche Intelligenz（KI）", "intelligence artificielle（IA）", "inteligencia artificial（IA）", "искусственный интеллект（ИИ）", "intelligenza artificiale（IA）"),
    ("machine learning", "机器学习（ML）", "機械学習（ML）", "머신러닝（ML）", "maschinelles Lernen（ML）", "apprentissage automatique（ML）", "aprendizaje automático（ML）", "машинное обучение（МО）", "apprendimento automatico（ML）"),
    ("deep learning", "深度学习", "ディープラーニング/深層学習", "딥러닝", "Deep Learning/tiefes Lernen", "apprentissage profond", "aprendizaje profundo", "глубокое обучение", "apprendimento profondo"),
    ("large language model", "大语言模型（LLM）", "大規模言語モデル（LLM）", "거대언어모델（LLM）", "großes Sprachmodell（LLM）", "grand modèle linguistique（LLM）", "modelo de lenguaje grande（LLM）", "большая языковая модель（LLM）", "modello linguistico di grandi dimensioni（LLM）"),
    ("LLM", "大语言模型", "LLM", "LLM", "LLM", "LLM", "LLM", "LLM", "LLM"),
    ("natural language processing", "自然语言处理（NLP）", "自然言語処理（NLP）", "자연어 처리（NLP）", "Verarbeitung natürlicher Sprache（NLP）", "traitement du langage naturel（TAL）", "procesamiento del lenguaje natural（PLN）", "обработка естественного языка（NLP）", "elaborazione del linguaggio naturale（NLP）"),
    ("cloud computing", "云计算", "クラウドコンピューティング", "클라우드 컴퓨팅", "Cloud Computing", "informatique en nuage/cloud computing", "computación en la nube", "облачные вычисления", "cloud computing"),
    ("microservices", "微服务架构", "マイクロサービス", "마이크로서비스", "Microservices", "microservices", "microservicios", "микросервисная архитектура", "microservizi"),
    ("distributed system", "分布式系统", "分散システム", "분산 시스템", "verteiltes System", "système distribué", "sistema distribuido", "распределенная система", "sistema distribuito"),
    ("cybersecurity", "网络安全", "サイバーセキュリティ", "사이버 보안", "Cybersicherheit", "cybersécurité", "ciberseguridad", "кибербезопасность", "sicurezza informatica")
]

merge_terms("tech_terms.json", tech_additions)

print("All dictionaries updated cleanly and successfully!")
