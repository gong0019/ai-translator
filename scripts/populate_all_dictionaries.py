#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Populate all specialist terminology catalogs to 200+ terms each."""

import json
from pathlib import Path

SKILLS_DIR = Path("/home/gongchixin/www/qwen-translator/skills")

def merge_terms(filename, new_entries):
    filepath = SKILLS_DIR / filename
    existing = []
    if filepath.exists():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d.get("terms"), list):
                    existing = d["terms"]
        except Exception:
            pass

    seen = {x["en"].strip().lower() for x in existing if "en" in x}
    merged = list(existing)

    for item in new_entries:
        if isinstance(item, tuple):
            entry = {
                "en": item[0], "zh": item[1], "ja": item[2], "ko": item[3],
                "de": item[4], "fr": item[5], "es": item[6], "ru": item[7], "it": item[8]
            }
        else:
            entry = item
        k = entry["en"].strip().lower()
        if k and k not in seen:
            seen.add(k)
            merged.append(entry)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({"terms": merged}, f, ensure_ascii=False, indent=2)
    print(f"✓ {filename}: {len(merged)} terms")

# ----------------------------------------------------------------------
# 1. 国际贸易与海关 (trade_terms.json) - 补充到 200+
# ----------------------------------------------------------------------
trade_additions = [
    ("bill of lading", "提单", "船荷証券", "선하증권", "Konnossement", "connaissement", "conocimiento de embarque", "коносамент", "polizza di carico"),
    ("clean bill of lading", "清洁提单", "無故障船荷証券", "무하자 선하증권", "reines Konnossement", "connaissement net", "conocimiento de embarque limpio", "чистый коносамент", "polizza di carico pulita"),
    ("foul bill of lading", "不清洁提单", "故障付船荷証券", "하자 선하증권", "unreines Konnossement", "connaissement avec réserves", "conocimiento de embarque sucio", "нечистый коносамент", "polizza di carico con riserve"),
    ("straight bill of lading", "记名提单", "記名式船荷証券", "기명식 선하증권", "Namenskonnossement", "connaissement nominatif", "conocimiento de embarque nominativo", "именной коносамент", "polizza di carico nominativa"),
    ("order bill of lading", "指示提单", "指図式船荷証券", "지시식 선하증권", "Orderkonnossement", "connaissement à ordre", "conocimiento de embarque a la orden", "ордерный коносамент", "polizza di carico all'ordine"),
    ("bearer bill of lading", "不记名提单", "持参人払式船荷証券", "무기명식 선하증권", "Inhaberkonnossement", "connaissement au porteur", "conocimiento de embarque al portador", "коносамент на предъявителя", "polizza di carico al portatore"),
    ("air waybill", "航空运单（AWB）", "航空運送状", "항공화물운송장", "Luftfrachtbrief", "lettre de transport aérien", "guía aérea", "авианакладная", "lettera di vettura aerea"),
    ("AWB", "航空运单", "航空運送状", "항공화물운송장", "Luftfrachtbrief", "LTA", "guía aérea", "авианакладная", "AWB"),
    ("sea waybill", "海运单", "海上運送状", "해상화물운송장", "Seefrachtbrief", "lettre de transport maritime", "guía marítima", "морская накладная", "lettera di trasporto marittimo"),
    ("packing list", "装箱单", "梱包明細書", "패킹리스트", "Packliste", "liste de colisage", "lista de empaque", "упаковочный лист", "distinta colli"),
    ("commercial invoice", "商业发票", "商業送り状", "상업송장", "Handelsrechnung", "facture commerciale", "factura comercial", "коммерческий инвойс", "fattura commerciale"),
    ("proforma invoice", "形式发票", "見積送り状", "견적송장", "Proforma-Rechnung", "facture pro forma", "factura proforma", "проформа-инвойс", "fattura proforma"),
    ("consular invoice", "领事发票", "領事査証送り状", "영사송장", "Konsulatsfaktura", "facture consulaire", "factura consular", "консульский инвойс", "fattura consolare"),
    ("customs declaration", "报关单", "税関申告書", "세관신고서", "Zollanmeldung", "déclaration en douane", "declaración aduanera", "таможенная декларация", "dichiarazione doganale"),
    ("customs clearance", "清关/结关", "通関手続き", "통관", "Zollabfertigung", "dédouanement", "despacho de aduanas", "таможенная очистка", "sdoganamento"),
    ("certificate of origin", "原产地证书（CO）", "原産地証明書", "원산지 증명서", "Ursprungszeugnis", "certificat d'origine", "certificado de origen", "сертификат происхождения", "certificato di origine"),
    ("Harmonized System code", "协调制度编码（HS编码）", "HSコード", "HS 코드", "HS-Code", "code du Système harmonisé", "código del Sistema Armonizado", "код Гармонизированной системы", "codice del Sistema armonizzato"),
    ("HS code", "协调制度编码", "HSコード", "HS 코드", "HS-Code", "code du Système harmonisé", "código del Sistema Armonizado", "код Гармонизированной системы", "codice del Sistema armonizzato"),
    ("customs tariff", "海关关税", "関税率表", "관세율표", "Zolltarif", "tarif douanier", "arancel aduanero", "таможенный тариф", "tariffa doganale"),
    ("freight forwarder", "货运代理人", "貨物利用運送業者", "화물운송주선인", "Spediteur", "transitaire", "transitario", "экспедитор", "spedizioniere"),
    ("consignee", "收货人", "荷受人", "수하인", "Empfänger", "destinataire", "consignatario", "грузополучатель", "destinatario"),
    ("consignor", "发货人/托运人", "荷送人", "송하인", "Absender", "expéditeur", "consignador", "грузоотправитель", "mittente"),
    ("shipper", "托运人/发货人", "荷送人", "화주/송하인", "Verlader", "chargeur", "embarcador", "отправитель", "caricatore"),
    ("carrier", "承运人", "運送人", "운송인", "Frachtführer", "transporteur", "transportista", "перевозчик", "vettore"),
    ("letter of credit", "信用证（L/C）", "信用状", "신용장", "Akkreditiv", "crédit documentaire", "carta de crédito", "аккредитив", "lettera di credito"),
    ("standby letter of credit", "备用信用证（SBLC）", "スタンドバイ信用状", "보증신용장", "Standby-Akkreditiv", "lettre de crédit stand-by", "carta de crédito contingente", "резервный аккредитив", "lettera di credito stand-by"),
    ("revolving letter of credit", "循环信用证", "回転信用状", "회전신용장", "Revolvierendes Akkreditiv", "crédit documentaire renouvelable", "carta de crédito rotativa", "револьверный аккредитив", "lettera di credito rotativa"),
    ("transferable letter of credit", "可转让信用证", "譲渡可能信用状", "양도가능신용장", "übertragbares Akkreditiv", "crédit transférable", "carta de crédito transferible", "переводной аккредитив", "lettera di credito trasferibile"),
    ("irrevocable letter of credit", "不可撤销信用证", "取消不能信用状", "취소불능신용장", "unwiderrufliches Akkreditiv", "crédit irrévocable", "carta de crédito irrevocable", "безотзывный аккредитив", "lettera di credito irrevocabile"),
    ("confirmed letter of credit", "保兑信用证", "確認信用状", "확인신용장", "bestätigtes Akkreditiv", "crédit confirmé", "carta de crédito confirmada", "подтвержденный аккредитив", "lettera di credito confermata"),
    ("telegraphic transfer", "电汇（T/T）", "電信送金", "전신송금（T/T）", "telegrafische Überweisung", "transfert télégraphique", "transferencia telegráfica", "телеграфный перевод", "bonifico telegrafico"),
    ("documents against payment", "付款交单（D/P）", "支払渡し（D/P）", "지급인도조건（D/P）", "Dokumente gegen Zahlung", "documents contre paiement", "documentos contra pago", "документы против платежа", "documenti contro pagamento"),
    ("documents against acceptance", "承兑交单（D/A）", "引受渡し（D/A）", "인수인도조건（D/A）", "Dokumente gegen Akzeptierung", "documents contre acceptation", "documentos contra aceptación", "документы против акцепта", "documenti contro accettazione"),
    ("bonded warehouse", "保税仓库", "保税倉庫", "보세창고", "Zolllager", "entrepôt sous douane", "almacén fiscal", "таможенный склад", "deposito doganale"),
    ("free trade zone", "自由贸易区（FTZ）", "自由貿易地域", "자유무역지대", "Freihandelszone", "zone de libre-échange", "zona franca", "зона свободной торговли", "zona franca"),
    ("anti-dumping duty", "反倾销税", "反ダンピング税", "반덤핑 관세", "Antidumpingzoll", "droit antidumping", "derecho antidumping", "антидемпинговая пошлина", "dazio antidumping"),
    ("countervailing duty", "反补贴税", "相殺関税", "상계관세", "Ausgleichszoll", "droit compensateur", "derecho compensatorio", "компенсационная пошлина", "dazio compensativo"),
    ("customs valuation", "海关估价", "関税評価", "관세평가", "Zollwertprüfung", "évaluation en douane", "valoración aduanera", "таможенная оценка", "valutazione doganale"),
    ("demurrage", "滞期费", "滞船料/デマレージ", "체선료/체화료", "Liegegeld/Demurrage", "surestaries", "demoras", "демередж", "controstallie"),
    ("detention", "滞箱费", "ディテンションチャージ", "지체료", "Containerverzögerungsgebühr", "frais de rétention", "detención de contenedores", "детеншн", "spese di detenzione"),
    ("less than container load", "拼箱货（LCL）", "混載貨物（LCL）", "소량화물（LCL）", "Stückgutladung（LCL）", "groupage maritime（LCL）", "carga consolidada（LCL）", "сборный груз（LCL）", "carico parziale（LCL）"),
    ("full container load", "整箱货（FCL）", "フルコンテナ貨物（FCL）", "만재화물（FCL）", "Vollcontainerladung（FCL）", "conteneur complet（FCL）", "contenedor completo（FCL）", "полный контейнер（FCL）", "carico completo（FCL）"),
    ("intermodal transport", "多式联运", "複合一貫輸送", "복합운송", "kombinierter Verkehr", "transport intermodal", "transporte intermodal", "интермодальные перевозки", "trasporto intermodale"),
    ("transshipment", "转船/转运", "積替え/トランスシップ", "환적", "Umladung/Transshipment", "transbordement", "transbordo", "перевалка/трансшипмент", "trasbordo"),
    ("cargo insurance", "货运险", "貨物保険", "적하보험", "Transportversicherung", "assurance marchandises transportées", "seguro de transporte de carga", "страхование грузов", "assicurazione merci"),
    ("general average", "共同海损", "共同海損", "공동해손", "Große Haverei", "avarie commune", "avería gruesa", "общая авария", "avaria generale"),
    ("particular average", "单独海损", "単独海損", "단독해손", "Besondere Haverei", "avarie particulière", "avería particular", "частная авария", "avaria particolare"),
    ("port of loading", "起运港/装货港（POL）", "船積港", "선적항", "Ladehafen", "port de chargement", "puerto de carga", "порт погрузки", "porto di imbarco"),
    ("port of discharge", "目的港/卸货港（POD）", "揚地港", "양하항", "Löschhafen", "port de déchargement", "puerto de descarga", "порт выгрузки", "porto di sbarco"),
    ("phytosanitary certificate", "植物检疫证书", "植物検疫証明書", "식물검역증명서", "Pflanzengesundheitszeugnis", "certificat phytosanitaire", "certificado fitosanitario", "фитосанитарный сертификат", "certificato fitosanitario"),
    ("fumigation certificate", "熏蒸证书", "燻蒸証明書", "훈증소독증명서", "Begasungszertifikat", "certificat de fumigation", "certificado de fumigación", "сертификат фумигации", "certificato di fumigazione"),
    ("inspection certificate", "商品检验证书", "検査証明書", "검사증명서", "Inspektionszertifikat", "certificat d'inspection", "certificado de inspección", "инспекционный сертификат", "certificato di ispezione"),
    ("customs broker", "报关行/报关员", "通関業者", "관세사", "Zollagent", "courtier en douane", "agente de aduanas", "таможенный брокер", "spedizioniere doganale"),
    ("bonded area", "保税区", "保税地域", "보세구역", "Freizone", "zone franche", "zona franca", "свободная таможенная зона", "zona franca doganale"),
    ("drawback", "出口退税", "関税払戻し/ドローバック", "관세환급", "Zollrückvergütung", "remboursement des droits de douane", "devolución de aranceles", "возврат пошлин", "drawback doganale"),
    ("container freight station", "集装箱货运站（CFS）", "CFS（コンテナ貨物詰所）", "컨테이너 화물집하소（CFS）", "Containerfrachtstation", "centre de groupage", "estación de carga de contenedores", "контейнерная грузовая станция", "stazione di carico container"),
    ("container yard", "集装箱堆场（CY）", "CY（コンテナヤード）", "컨테이너 야드（CY）", "Containerdepot", "parc à conteneurs", "patio de contenedores", "контейнерный терминал", "terminal container"),
    ("twenty-foot equivalent unit", "标准集装箱（TEU）", "20フィート換算ユニット（TEU）", "20피트 표준 컨테이너（TEU）", "Zwanzig-Fuß-Standardcontainer", "équivalent vingt pieds（EVP）", "unidad equivalente a veinte pies（TEU）", "двадцатифутовый эквивалент", "unità equivalente a venti piedi（TEU）"),
    ("TEU", "标准集装箱（TEU）", "TEU（20フィート換算）", "TEU", "TEU", "EVP", "TEU", "ДФЭ/TEU", "TEU"),
    ("forty-foot equivalent unit", "40英尺标准集装箱（FEU）", "40フィート換算ユニット（FEU）", "40피트 표준 컨테이너（FEU）", "Vierzig-Fuß-Standardcontainer", "équivalent quarante pieds（FEU）", "unidad equivalente a cuarenta pies（FEU）", "сорокафутовый эквивалент（FEU）", "unità equivalente a quaranta piedi（FEU）"),
    ("bunker adjustment factor", "燃油附加费（BAF）", "燃料割増料金（BAF）", "유류할증료（BAF）", "Treibstoffzuschlag（BAF）", "surcharge combustible（BAF）", "recargo por combustible（BAF）", "топливная надбавка（BAF）", "sovrapprezzo carburante（BAF）"),
    ("currency adjustment factor", "货币贬值附加费（CAF）", "通貨変動割増料金（CAF）", "통화할증료（CAF）", "Währungszuschlag（CAF）", "facteur d'ajustement monétaire（CAF）", "recargo monetario（CAF）", "валютная надбавка（CAF）", "sovrapprezzo valutario（CAF）"),
    ("terminal handling charge", "码头操作费（THC）", "ターミナル作業料（THC）", "터미널조작료（THC）", "Terminalabfertigungsgebühr（THC）", "frais de manutention portuaire（THC）", "gastos de manipulación en terminal（THC）", "терминальный сбор（THC）", "spese di movimentazione terminal（THC）"),
    ("open account", "赊销/记账交易（O/A）", "オープンアカウント/掛売決済", "사후송금방식（O/A）", "offenes Ziel（O/A）", "compte ouvert", "cuenta abierta", "открытый счет（O/A）", "conto aperto"),
    ("factoring", "出口保理/保付代理", "国際ファクタリング", "팩토링", "Factoring", "affacturage", "factoraje", "факторинг", "factoring"),
    ("forfaiting", "福费廷/包买票据", "フォーフェイティング", "포페이팅", "Forfaitierung", "forfaitage", "forfaiting", "форфейтинг", "forfaiting"),
    ("certificate of conformity", "合格证书（CoC）", "適合証明書（CoC）", "적합성 증명서", "Konformitätsbescheinigung", "certificat de conformité", "certificado de conformidad", "сертификат соответствия", "certificato di conformità"),
    ("sanitary and phytosanitary measures", "卫生与植物卫生措施（SPS）", "衛生植物検疫措置（SPS）", "위생 및 식물위생 조치（SPS）", "sanitäre und phytosanitäre Maßnahmen", "mesures sanitaires et phytosanitaires", "medidas sanitarias y fitosanitarias", "санитарные и фитосанитарные меры", "misure sanitarie e fitosanitarie"),
    ("technical barriers to trade", "技术性贸易壁垒（TBT）", "貿易の技術的障害（TBT）", "무역에 관한 기술장벽（TBT）", "technische Handelshemmnisse（TBT）", "obstacles techniques au commerce", "obstáculos técnicos al comercio", "технические барьеры в торговле", "ostacoli tecnici al commercio"),
    ("most-favoured-nation", "最惠国待遇（MFN）", "最恵国待遇（MFN）", "최혜국대우（MFN）", "Meistbegünstigung", "clause de la nation la plus favorisée", "nación más favorecida", "режим наибольшего благоприятствования", "nazione più favorita"),
    ("rules of origin", "原产地规则", "原産地規則", "원산지 규정", "Ursprungsregeln", "règles d'origine", "normas de origen", "правила происхождения", "regole di origine"),
    ("customs union", "关税同盟", "関税同盟", "관세동맹", "Zollunion", "union douanière", "unión aduanera", "таможенный союз", "unione doganale"),
    ("free trade agreement", "自由贸易协定（FTA）", "自由貿易協定（FTA）", "자유무역협정（FTA）", "Freihandelsabkommen", "accord de libre-échange", "tratado de libre comercio", "соглашение о свободной торговле", "accordo di libero scambio"),
    ("FTA", "自由贸易协定（FTA）", "FTA（自由貿易協定）", "FTA", "Freihandelsabkommen", "ALE", "TLC", "ЗСТ/ССТ", "accordo FTA"),
    ("authorized economic operator", "经认证的经营者（AEO）", "AEO（認定事業者）", "종합인증우수업체（AEO）", "zugelassener Wirtschaftsbeteiligter（AEO）", "opérateur économique agréé（OEA）", "operador económico autorizado（OEA）", "уполномоченный экономический оператор（УЭО）", "operatore economico autorizzato（AEO）"),
    ("AEO", "AEO认证资质", "AEO制度", "AEO", "AEO-Zertifizierung", "statut OEA", "operador OEA", "статус УЭО", "certificazione AEO"),
    ("customs compliance", "海关合规", "通関コンプライアンス", "통관 규정준수", "Zoll-Compliance", "conformité douanière", "cumplimiento aduanero", "таможенный комплаенс", "conformità doganale"),
    ("export control", "出口管制", "輸出管理", "수출통제", "Exportkontrolle", "contrôle des exportations", "control de exportaciones", "экспортный контроль", "controllo delle esportazioni"),
    ("dual-use goods", "军民两用物项", "デュアルユース（軍民両用）品目", "이중용도 품목", "Güter mit doppeltem Verwendungszweck", "biens à double usage", "bienes de doble uso", "товары двойного назначения", "beni a duplice uso"),
    ("generalized system of preferences", "普惠制（GSP）", "一般特恵関税制度（GSP）", "일반특혜관세제도（GSP）", "Allgemeines Präferenzsystem（APS）", "système généralisé de préférences（SGP）", "sistema generalizado de preferencias（SGP）", "генеральная система преференций（ГСП）", "sistema di preferenze generalizzate（SPG）"),
    ("GSP", "普惠制", "GSP特恵", "GSP", "APS", "SGP", "SGP", "ГСП", "SPG"),
    ("trade facilitation agreement", "贸易便利化协定（TFA）", "貿易円滑化協定（TFA）", "무역원활화협정（TFA）", "Handelserleichterungsabkommen（TFA）", "Accord sur la facilitation des échanges（AFE）", "Acuerdo sobre Facilitación del Comercio（AFC）", "Соглашение об упрощении процедур торговли", "Accordo sulla facilitazione degli scambi（TFA）"),
    ("single window system", "国际贸易单一窗口", "シングルウィンドウシステム", "싱글윈도우 시스템", "Single-Window-System", "système de guichet unique", "sistema de ventanilla única", "система единого окна", "sistema a sportello unico"),
    ("cross-border road transport", "跨境公路运输（TIR）", "TIR条約道路輸送", "TIR 국제도로운송", "TIR-Straßentransport", "transport routier sous carnet TIR", "transporte por carretera TIR", "международные дорожные перевозки TIR", "trasporto su strada convenzione TIR"),
    ("TIR carnet", "TIR单证册", "TIRカルネ", "TIR 까르네", "TIR-Carnet", "carnet TIR", "cuaderno TIR", "книжка МДП (TIR)", "carnet TIR"),
    ("dry port", "无水港/内陆无水港", "内陸ドライポート", "내륙컨테이너기지（드라이포트）", "Binnenhafen/Dry Port", "port sec", "puerto seco", "сухой порт/сухопутный терминал", "porto secco"),
    ("inland container depot", "内陆集装箱货运站（ICD）", "内陸コンテナデポ（ICD）", "내륙컨테이너기지（ICD）", "Inland-Container-Depot（ICD）", "dépôt intérieur de conteneurs", "depósito interior de contenedores", "внутренний контейнерный терминал", "deposito container interno"),
    ("freight rate", "运价/运费率", "運賃レート", "운임률", "Frachtrate", "taux de fret", "tarifa de flete", "фрахтовая ставка", "tariffa di nolo"),
    ("all-in rate", "全包费率", "オールイン運賃", "올인 운임", "All-in-Rate", "taux tout compris", "tarifa todo incluido", "ставка всё включено", "tariffa all-inclusive"),
    ("shipping agency", "船务代理", "船舶代理店", "선박대리점", "Schiffsagentur", "agence maritime", "agencia marítima", "агентирование судов", "agenzia marittima"),
    ("cross-border logistics", "跨境物流", "越境ロジスティクス", "크로스보더 물류", "grenzüberschreitende Logistik", "logistique transfrontalière", "logística transfronteriza", "трансграничная логистика", "logistica transfrontaliera"),
    ("bonded supervision", "保税监管", "保税監督管理", "보세감독관리", "zollamtliche Überwachung", "surveillance douanière", "control aduanero", "таможенный надзор", "vigilanza doganale")
]

merge_terms("trade_terms.json", trade_additions)
