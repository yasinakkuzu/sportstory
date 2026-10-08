import os
import re
import json
import random
import logging
import requests
from dotenv import load_dotenv
from engine.schemas import AutoScriptPayload, AutoScenePlan

load_dotenv()
logger = logging.getLogger("AntigravityEngine.ScriptWeaver")


def parse_json_robustly(raw_text: str) -> dict:
    """
    Gemini çıktılarındaki kaçışsız kontrol karakterlerini, satır başlarını ve
    markdown formatlama artıklarını temizleyerek JSON ayrıştırması yapar.
    """
    if not raw_text:
        raise ValueError("Boş model yanıtı")

    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # En dıştaki JSON objesini yakala
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    # 1. Deneme: strict=False ile ayrıştırma (unescaped newline/control char'ları tolere eder)
    try:
        return json.loads(text, strict=False)
    except Exception:
        pass

    # 2. Deneme: Tırnak içerisindeki ham yeni satırları ve sekmeleri kaçış karakterine çevir
    try:
        def clean_control_chars(m):
            s = m.group(0)
            return s.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

        cleaned = re.sub(r'"(?:[^"\\]|\\.)*"', clean_control_chars, text)
        return json.loads(cleaned, strict=False)
    except Exception as e:
        raise ValueError(f"JSON ayrıştırma kurtarılamadı: {e}")


MASTER_KNOWLEDGE_FALLBACKS = {
    "city": {
        "title_tr": "Man City: 115 Kural İhlali Davası! 🚨⚖️ #shorts",
        "description_tr": "Manchester City 115 mali kural ihlali suçlamasıyla yüzyılın davasında! Şampiyonlukları silinebilir mi yoksa küme mi düşürülecekler? 🔔 Futbol skandalları ve finans hikayeleri için @SportStoryTR kanalına abone olun. #shorts #futbol #mancity #premierleague #sporfinansı",
        "tags_tr": ["shorts", "futbol", "manchester city", "man city", "premier lig", "115 kural ihlali", "spor finansı", "pep guardiola"],
        "title_en": "Man City: The 115 Charges Trial! 🚨⚖️ #shorts",
        "description_en": "Manchester City is currently facing the Premier League's trial of the century with 115 financial breach charges. Could the champions be stripped of titles or face automatic relegation? 🔔 Subscribe to @SportStory for daily football finance & scandal stories. #shorts #football #mancity #premierleague #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "man city", "premier league", "115 charges", "sports finance", "pep guardiola"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Manchester City dominates world football, but an unprecedented trial threatens to destroy their entire modern legacy.", "text_tr": "Manchester City dünya futbolunu domine ediyor ancak benzeri görülmemiş bir duruşma tüm mirasını yok etmekle tehdit ediyor.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Facing one hundred and fifteen financial charges, City is accused of disguising millions in illicit owner funding.", "text_tr": "Yüz on beş mali kural ihlaliyle suçlanan City, kulüp sahibinin milyonlarını sahte sponsorluklarla gizlemekle suçlanıyor.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Premier League rivals are demanding severe penalties, ranging from massive points deductions to total league expulsion.", "text_tr": "Premier Lig rakipleri devasa puan silme cezalarından ligden ihraç edilmeye kadar en ağır yaptırımları talep ediyor.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Top defense lawyers earning thousands per hour are currently battling behind closed doors in London.", "text_tr": "Saatte binlerce sterlin kazanan en iyi savunma avukatları Londra'da kapalı kapılar ardında savaşıyor.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "If found guilty, should Manchester City be relegated from the Premier League? Comment your verdict below!", "text_tr": "Eğer suçlu bulunursa Manchester City Premier Lig'den küme düşürülmeli mi? Fikrini yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "vinicius": {
        "title_tr": "Vinicius Jr: 1 Milyar Dolarlık Suudi Teklifi! 💸🇸🇦 #shorts",
        "description_tr": "Suudi Arabistan Vinicius Junior'a spor tarihinin en büyük sözleşmesini teklif etti. Real Madrid yıldızı 1 milyar euroyu seçecek mi? 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #realmadrid #vinicius #transfer #sporfinansı",
        "tags_tr": ["shorts", "futbol", "vinicius", "real madrid", "suudi arabistan", "spor finansı", "transferler"],
        "title_en": "Vinicius Jr: The $1B Saudi Dilemma! 💸🇸🇦 #shorts",
        "description_en": "Saudi Arabia tabled an unprecedented €1 Billion total package for Vinicius Junior. Will Real Madrid's superstar take the biggest contract in sports history? 🔔 Subscribe to @SportStory for daily football finance & scandal stories. #shorts #football #realmadrid #vinicius #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "vinicius", "real madrid", "saudi pro league", "sports finance", "transfers"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Real Madrid superstar Vinicius Junior was handed the most lucrative financial proposal in world sports history.", "text_tr": "Real Madrid süper yıldızı Vinicius Junior'a dünya spor tarihinin en kazançlı finansal teklifi sunuldu.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Saudi Arabia's sovereign wealth fund presented a staggering one-billion-euro five-year total contract package.", "text_tr": "Suudi Arabistan Varlık Fonu toplamda bir milyar euroluk akıl almaz beş yıllık bir sözleşme paketi masaya koydu.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Accepting would pay him two hundred million euros annually, completely shattering every existing global wage record.", "text_tr": "Kabul etmesi yılda iki yüz milyon euro kazanması ve var olan tüm küresel maaş rekorlarını kırması anlamına geliyor.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Yet walking away from the Bernabéu means sacrificing Champions League dominance and guaranteed Ballon d'Or glory.", "text_tr": "Ancak Bernabeu'dan ayrılmak Şampiyonlar Ligi zaferlerini ve garanti Ballon d'Or yarışını feda etmek demek.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Would you choose one billion euros or football immortality with Real Madrid? Let us know below!", "text_tr": "Sen olsan bir milyar euroyu mu yoksa Real Madrid ile futbol ölümsüzlüğünü mü seçerdin? Yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "inter": {
        "title_tr": "Inter Milan: 400M€ Borcun Çaldığı Dev! 📉 #shorts",
        "description_tr": "Inter Serie A şampiyonu oldu ancak Çinli sahip Suning, Amerikan fonu Oaktree'ye 395 milyon euroluk borcunu ödeyemeyince kulübü kaybetti. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #inter #seriea #sporfinansı",
        "tags_tr": ["shorts", "futbol", "inter milan", "serie a", "oaktree", "suning", "spor finansı"],
        "title_en": "Inter Milan: How A €400M Debt Stole A Giant! 📉 #shorts",
        "description_en": "Inter Milan won Serie A, but Chinese owners Suning defaulted on a €395M emergency loan to Oaktree Capital, losing the club overnight. 🔔 Subscribe to @SportStory for daily football finance & scandal stories. #shorts #football #inter #seriea #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "inter milan", "serie a", "oaktree", "suning", "sports finance"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Inter Milan celebrated winning their twentieth Serie A title while privately facing total financial foreclosure.", "text_tr": "Inter Milan 20. Serie A şampiyonluğunu kutlarken kapalı kapılar ardında kulübe el konulması tehlikesiyle yüzleşti.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Chinese ownership group Suning borrowed nearly four hundred million euros from American fund Oaktree Capital.", "text_tr": "Çinli Suning grubu Amerikan yatırım fonu Oaktree'den yaklaşık dört yüz milyon euro borç aldı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "When crippling interest rates struck, Suning failed to repay the emergency debt before the deadline.", "text_tr": "Yüksek faizler ve son ödeme tarihi geldiğinde Suning bu acil durum kredisini geri ödeyemedi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Oaktree seized complete control of the Italian champions overnight, wiping out Suning's entire multi-million investment.", "text_tr": "Oaktree bir gecede İtalyan şampiyonunun tüm kontrolünü devraldı ve Suning'in dev yatırımını sildi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Are American hedge funds taking over European football for better or worse? Comment below!", "text_tr": "Amerikan fonlarının Avrupa futbolunu ele geçirmesi iyi mi kötü mü? Yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "aston villa": {
        "title_tr": "Aston Villa: 100M€ Harcama Sınırı Çıkmazı! 🚨💸 #shorts",
        "description_tr": "Aston Villa Şampiyonlar Ligi'ne kaldı ancak Premier Lig'in PSR harcama sınırlarına çarparak acil satış yapmak zorunda kaldı. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #astonvilla #premierleague #psr",
        "tags_tr": ["shorts", "futbol", "aston villa", "premier lig", "psr", "spor finansı", "unai emery"],
        "title_en": "Aston Villa: The €100M PSR Red Line! 🚨💸 #shorts",
        "description_en": "Aston Villa qualified for the Champions League, only to face strict Premier League PSR spending limits and emergency player fire sales. 🔔 Subscribe to @SportStory for daily football finance & scandal stories. #shorts #football #astonvilla #premierleague #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "aston villa", "premier league", "psr", "sports finance", "unai emery"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Aston Villa stormed into the Champions League, yet immediately crashed into the Premier League's spending limits.", "text_tr": "Aston Villa Şampiyonlar Ligi'ne fırtına gibi girdi ancak hemen Premier Lig'in harcama sınırlarına çarptı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "PSR regulations forced Villa to generate sixty million pounds before the June thirtieth accounting deadline.", "text_tr": "Mali kurallar Villa'yı 30 Haziran bilanço tarihinden önce 60 milyon sterlin gelir yaratmaya zorladı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "To avoid severe points deductions, they sold Douglas Luiz in an emergency multi-club swap deal.", "text_tr": "Ağır puan silme cezasından kaçınmak için Douglas Luiz'i acil takas anlaşmasıyla satmak zorunda kaldılar.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Despite billionaire owners, strict financial rules prevent ambitious clubs from challenging the established elite.", "text_tr": "Milyarder sahiplerine rağmen katı kurallar hırslı kulüplerin geleneksel elitlere meydan okumasını engelliyor.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Do spending caps protect football clubs or simply preserve the traditional big six? Share your verdict!", "text_tr": "Harcama sınırları kulüpleri mi koruyor yoksa sadece geleneksel devleri mi kayırıyor? Yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "anzhi": {
        "title_tr": "Anzhi: Bir Milyar Dolarlık Rüyanın Sonu! 📉 #shorts",
        "description_tr": "Süleyman Kerimov, Samuel Eto'o ve Roberto Carlos'a yüz milyonlar akıttı ancak bir gecede kulübü tasfiye etti. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #anzhi #etoo #robertocarlos #sporfinansı",
        "tags_tr": ["shorts", "futbol", "anzhi", "etoo", "roberto carlos", "spor finansı", "skandal"],
        "title_en": "Anzhi: The Billion-Dollar Dream That Died! 📉 #shorts",
        "description_en": "Suleyman Kerimov spent hundreds of millions on Samuel Eto'o and Roberto Carlos, only to liquidate the Russian superclub overnight. 🔔 Subscribe to @SportStory for daily football finance & scandal stories. #shorts #football #anzhi #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "anzhi", "etoo", "roberto carlos", "sports finance", "scandal"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Russian billionaire Suleyman Kerimov promised to conquer Europe by pouring hundreds of millions into Anzhi.", "text_tr": "Rus milyarder Süleyman Kerimov Anzhi'ye yüz milyonlarca euro akıtarak Avrupa'yı fethetme sözü verdi.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "He signed Samuel Eto'o on world-record wages and flew players to Dagestan only for matches.", "text_tr": "Samuel Eto'o'ya dünya rekoru maaş bağladı ve oyuncuları Dağıstan'a sadece maçlar için uçurdu.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Then overnight, Kerimov's business empire collapsed, slashing his fortune and sparking instant panic.", "text_tr": "Ardından bir gecede Kerimov'un iş imparatorluğu çöktü, serveti eridi ve anında panik başladı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "In a single week, Anzhi sold their entire superstar squad, plummeting into debt and eventual dissolution.", "text_tr": "Tek bir haftada Anzhi tüm süper yıldızlarını sattı, borç batağına ve nihai kapanışa sürüklendi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Was Anzhi the most ridiculous vanity project in football history? Let us know below!", "text_tr": "Anzhi futbol tarihinin en absürt kibrine kurban giden projesi miydi? Yorumlarda buluşalım!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "deportivo": {
        "title_tr": "Deportivo: Şampiyonlar Ligi'nden 3. Lige! 📉 #shorts",
        "description_tr": "Süper Depor Avrupa devlerini dize getirdi ancak 160 milyon euroluk borç kulübü 3. lige kadar sürükledi. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #deportivo #laliga #sporfinansı",
        "tags_tr": ["shorts", "futbol", "deportivo", "super depor", "la liga", "spor finansı"],
        "title_en": "Deportivo: From Champions League To Div 3! 📉 #shorts",
        "description_en": "Super Depor stunned Europe, but reckless debt over €160M caused two decades of suffering and third-tier relegation. 🔔 Subscribe to @SportStory for daily football finance & scandal stories. #shorts #football #deportivo #laliga #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "deportivo", "super depor", "la liga", "sports finance"],
        "scenes": [
            {"scene_idx": 1, "text_en": "In 2000, Deportivo La Coruna won La Liga, defeating Milan and Europe's biggest giants.", "text_tr": "2000 yılında Deportivo La Coruna Milan'ı ve Avrupa devlerini dize getirerek La Liga'yı kazandı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "President Lendoiro chased trophies by borrowing recklessly, accumulating one hundred and sixty million euros in debt.", "text_tr": "Başkan Lendoiro kupa peşinde kontrolsüz borçlandı ve kulübü 160 milyon euro borca soktu.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "When banks demanded repayment, Super Depor crashed into administration, unable to sign or keep talent.", "text_tr": "Bankalar paralarını geri isteyince Süper Depor kayyuma gitti ve oyuncularını elinde tutamadı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "The Spanish champions plummeted straight into the third division, spending decades fighting for survival.", "text_tr": "İspanyol şampiyonu doğrudan üçüncü lige kadar çakıldı ve hayatta kalmak için yıllarca savaştı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Will Deportivo ever reclaim their glory, or is modern football too brutal? Drop your thoughts!", "text_tr": "Deportivo eski günlerine dönebilir mi yoksa modern futbol çok mu acımasız? Fikrini yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "barcelona": {
        "title_tr": "Barcelona: 1 Milyar Euro Nasıl Battı? 💸📉 #shorts",
        "description_tr": "FC Barcelona Şampiyonlar Ligi kupalarından 1.35 milyar euroluk borç bataklığına nasıl sürüklendi? Lionel Messi'nin vedası ve mali kriz. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #barcelona #messi #sporfinansı",
        "tags_tr": ["shorts", "futbol", "barcelona", "messi", "spor finansı", "la liga"],
        "title_en": "How FC Barcelona Lost One Billion Euros! 💸📉 #shorts #football #barcelona",
        "description_en": "Witness the shocking financial collapse of FC Barcelona, from lifting Champions League trophies to drowning in 1.3 billion euros of catastrophic debt. How did a football empire nearly self-destruct? Watch till the end and join the debate in the comments! #shorts #football #soccer #barcelona #messi #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "barcelona", "messi", "sports finance", "la liga"],
        "scenes": [
            {"scene_idx": 1, "text_en": "FC Barcelona ruled world football, masking a dark financial catastrophe beneath glittering trophies.", "text_tr": "FC Barcelona parlak kupaların arkasında karanlık bir mali felaketi gizleyerek dünya futbolunu yönetti.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Reckless transfers like Coutinho and Griezmann collided with an astronomical, completely unsustainable wage bill.", "text_tr": "Coutinho ve Griezmann gibi kontrolsüz transferler astronomik ve sürdürülemez maaş bütçesiyle birleşti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "When the crisis hit, total club debts exploded past one point three billion euros.", "text_tr": "Kriz patladığında kulübün toplam borcu bir nokta üç milyar euroyu aştı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Lionel Messi was forced out in tears while directors desperately sold twenty-five years of future TV rights.", "text_tr": "Lionel Messi gözyaşları içinde ayrılmak zorunda kaldı ve yöneticiler 25 yıllık TV gelirlerini ipotek etti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Did Barcelona mortgage their entire future just to survive? Let us know in the comments below!", "text_tr": "Barcelona sadece hayatta kalmak için tüm geleceğini mi ipotek etti? Yorumlarda buluşalım!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "leeds": {
        "title_tr": "Leeds United: Akvaryum Balığından İflasa! 💸🚨 #shorts",
        "description_tr": "Leeds United Şampiyonlar Ligi yarı finalinden 3. lige ve iflasa nasıl yuvarlandı? 60 milyon sterlinlik borç kumarı. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #leedsunited #premierleague #sporfinansı",
        "tags_tr": ["shorts", "futbol", "leeds united", "premier lig", "spor finansı", "skandal"],
        "title_en": "Leeds United: The £60M Goldfish Bowl Bankruptcy! 💸🚨 #shorts #football",
        "description_en": "How did Leeds United go from the Champions League semi-finals to catastrophic financial ruin? Chairman Peter Ridsdale gambled £60 million on future TV revenue—and even leased goldfish for the boardroom at £20 a month. When they missed Europe, the club collapsed.\n\nSubscribe to SportStory for daily sports finance & football scandals.\n\n#shorts #football #soccer #leedsunited #premierleague #finance",
        "tags_en": ["shorts", "football", "soccer", "leeds united", "premier league", "sports finance", "scandal"],
        "scenes": [
            {"scene_idx": 1, "text_en": "In 2001, Leeds United reached the Champions League semi-finals. Three years later, they were completely bankrupt.", "text_tr": "2001'de Leeds United Şampiyonlar Ligi yarı finalindeydi. Üç yıl sonra tamamen iflas ettiler.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Chairman Peter Ridsdale gambled sixty million pounds on loans, even leasing goldfish for his office at twenty pounds a month.", "text_tr": "Başkan Peter Ridsdale 60 milyon sterlin borç aldı, hatta ofisindeki akvaryum balıklarını bile kiraladı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "When they failed to qualify for Europe, the debt exploded. They were forced to sell Rio Ferdinand and their entire squad.", "text_tr": "Avrupa kupalarına kalamayınca borç patladı. Rio Ferdinand ve tüm kadroyu yok pahasına sattılar.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Leeds crashed into the third tier, losing Elland Road and their training ground just to survive.", "text_tr": "Leeds üçüncü lige kadar düştü, hayatta kalmak için stadyumunu ve tesislerini bile kaybetti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "It took sixteen agonizing years to return. Is this the most reckless gamble in football history?", "text_tr": "Geri dönmeleri tam 16 acı dolu yıl sürdü. Bu futbol tarihinin en büyük kumarı mıydı?", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "juventus": {
        "title_tr": "Juventus: Sahte Muhasebe ve 15 Puan Silme! ⚖️🚨 #shorts",
        "description_tr": "Juventus'un 15 puanının silinmesine yol açan Plusvalenza sahte transfer değerleme skandalı. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #juventus #seriea #plusvalenza",
        "tags_tr": ["shorts", "futbol", "juventus", "serie a", "plusvalenza", "spor finansı"],
        "title_en": "Juventus: The Plusvalenza Secret Book Scandal! ⚖️🚨 #shorts #football",
        "description_en": "The shocking truth behind Juventus' 15-point penalty and the Plusvalenza scandal. How Italian prosecutors uncovered secret documents showing artificial capital gains on player swaps like Arthur and Pjanic.\n\nSubscribe to SportStory for deep dives into football finance.\n\n#shorts #football #soccer #juventus #seriea #scandal",
        "tags_en": ["shorts", "football", "soccer", "juventus", "serie a", "plusvalenza", "sports finance"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Italian police raided Juventus headquarters and discovered secret black books hidden in Turin.", "text_tr": "İtalyan polisi Juventus merkezini bastı ve Torino'da gizlenmiş gizli kara defterler buldu.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "To hide massive losses, Juventus inflated transfer values, swapping Arthur and Pjanic for fictitious seventy-million valuations.", "text_tr": "Büyük zararları gizlemek için Arthur ve Pjanic takasını 70 milyonluk sahte değerlerle şişirdiler.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Wiretapped phone calls caught directors admitting their balance sheets were completely fake.", "text_tr": "Dinlenen telefon kayıtlarında yöneticilerin bilançoların sahte olduğunu itiraf ettiği ortaya çıktı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "The entire board resigned in disgrace, and Juventus was slapped with a crushing fifteen-point deduction.", "text_tr": "Tüm yönetim kurulu utanç içinde istifa etti ve Juventus'un 15 puanı bir anda silindi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Was this corrupt accounting, or was Juventus just doing what every top club does secretly?", "text_tr": "Bu yozlaşmış bir muhasebe miydi, yoksa her kulübün gizlice yaptığını mı yaptılar?", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "chelsea": {
        "title_tr": "Chelsea: 1 Milyar Sterlinlik 8 Yıllık Hile! 🤯💸 #shorts",
        "description_tr": "Todd Boehly 18 ayda 1 milyar sterlin harcamak için 8 yıllık kontrat açığını nasıl kullandı? 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #chelsea #premierleague #transfer",
        "tags_tr": ["shorts", "futbol", "chelsea", "premier lig", "transfer", "boehly"],
        "title_en": "Chelsea: The £1 Billion 8-Year Contract Loophole! 🤯💸 #shorts #football",
        "description_en": "How Todd Boehly exploited the amortisation loophole to spend over £1 Billion in transfer fees using 8-year contracts, forcing UEFA to intervene and change international football rules.\n\nSubscribe to SportStory for daily sports finance breakdown.\n\n#shorts #football #soccer #chelsea #premierleague #transfer",
        "tags_en": ["shorts", "football", "soccer", "chelsea", "premier league", "transfer", "boehly"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Chelsea spent over one billion pounds in eighteen months, shattering all financial fair play records.", "text_tr": "Chelsea 18 ayda 1 milyar sterlinden fazla para harcayarak tüm finansal fair play rekorlarını yıktı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Todd Boehly unlocked a wild loophole: handing players unprecedented eight-year contracts to spread transfer costs.", "text_tr": "Todd Boehly çılgın bir açık buldu: transfer maliyetini yaymak için oyunculara 8 yıllık kontratlar verdi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Enzo Fernandez and Mudryk signed deals running until 2031, leaving rival clubs furious.", "text_tr": "Enzo Fernandez ve Mudryk 2031'e kadar süren sözleşmelere imza atarak rakipleri çıldırttı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "UEFA stepped in immediately, capping contract amortization at five years to close the loophole forever.", "text_tr": "UEFA acilen devreye girdi ve bu açığı sonsuza dek kapatmak için amortismanı 5 yılla sınırladı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Now Chelsea is trapped paying underperforming stars for a decade. Was Boehly a financial genius or reckless?", "text_tr": "Şimdi Chelsea bu yıldızlara 10 yıl ödeme yapma tuzağına düştü. Boehly dahi miydi yoksa deli mi?", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "everton": {
        "title_tr": "Everton: Çifte Puan Silme ve İflas Eşiği! 📉🚨 #shorts",
        "description_tr": "Everton'ın yeni stadyum borçları, 777 Partners fiyaskosu ve Premier Lig'de iki kez puan silme cezası alması. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #everton #premierleague #psr",
        "tags_tr": ["shorts", "futbol", "everton", "premier lig", "psr", "spor finansı"],
        "title_en": "Everton: The 777 Partners Disaster & Double Points Deduction! 📉🚨 #shorts #football",
        "description_en": "How Everton suffered two Premier League points deductions and nearly collapsed under catastrophic stadium debts and the chaotic 777 Partners takeover.\n\nSubscribe to SportStory for daily sports finance breakdowns.\n\n#shorts #football #everton #premierleague #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "everton", "premier league", "psr", "points deduction", "sports finance"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Everton is one of English football's founding giants, but reckless financial chaos pushed them to the brink of ruin.", "text_tr": "Everton İngiliz futbolunun kurucu devlerinden biridir, ancak kontrolsüz finansal kaos onları yıkımın eşiğine getirdi.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Under Farhad Moshiri, the club burned through over five hundred million pounds while building a massive new dockland stadium.", "text_tr": "Farhad Moshiri döneminde kulüp yeni stadyum inşa ederken 500 milyon sterlinden fazla para yaktı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Mounting debts breached Premier League profitability rules, triggering unprecedented double points deductions.", "text_tr": "Büyüyen borçlar Premier Lig kural sınırlarını aştı ve kulübe eşi görülmemiş iki kez puan silme cezası verildi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "A desperate takeover deal with Miami investment firm 777 Partners collapsed amid fraud lawsuits in New York.", "text_tr": "Miami merkezli 777 Partners ile yapılan kurtarma anlaşması New York'taki dolandırıcılık davalarıyla çöktü.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Can Everton survive their crushing stadium debt, or is relegation inevitable? Share your thoughts below!", "text_tr": "Everton bu devasa stadyum borcundan kurtulabilir mi, yoksa küme düşmek kaçınılmaz mı? Yorumlarda buluşalım!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "milan": {
        "title_tr": "AC Milan: 600M€ RedBird Borç Tuzağı! 🚨💸 #shorts",
        "description_tr": "AC Milan şampiyon oldu ama kulüp binasını basan mali polis ve RedBird ile Elliott arasındaki 600 milyonluk borç kıskacı. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #acmilan #seriea #sporfinansı",
        "tags_tr": ["shorts", "futbol", "ac milan", "serie a", "redbird", "elliott", "spor finansı"],
        "title_en": "AC Milan: The €600M RedBird Debt Trap! 🚨💸 #shorts #football",
        "description_en": "How AC Milan got caught between RedBird Capital and Elliott Management in a €600 million vendor loan debt trap that triggered Italian police raids.\n\nSubscribe to SportStory for daily sports finance.\n\n#shorts #football #acmilan #seriea #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "ac milan", "serie a", "redbird", "elliott", "sports finance"],
        "scenes": [
            {"scene_idx": 1, "text_en": "AC Milan won the Serie A title, but behind the celebrations lurked a sixty-million-euro hidden debt trap.", "text_tr": "AC Milan Serie A şampiyonluğunu kazandı ancak kutlamaların ardında 600 milyonluk gizli bir borç tuzağı vardı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Gerry Cardinale's RedBird bought the club by borrowing five hundred and fifty million euros directly from former owners Elliott.", "text_tr": "RedBird, kulübü eski sahibi Elliott Fonu'ndan 550 milyon euro borç alarak satın aldı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "When ballooning interest payments piled up, Italian financial police raided Milan's headquarters searching for true ownership records.", "text_tr": "Faiz ödemeleri birikirken, İtalyan mali polisi gerçek sahip belgelerini aramak için Milan kulüp binasını bastı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "With high interest rates squeezing every transfer window, the Rossoneri face losing key stars or ceding control.", "text_tr": "Yüksek faizler her transfer dönemini kısıtlarken Milan yıldızlarını satma veya yönetimi devretme tehlikesiyle karşı karşıya.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Is RedBird building an empire, or will Elliott seize AC Milan once again? Comment your prediction!", "text_tr": "RedBird bir imparatorluk mu kuruyor yoksa Elliott Milan'a yeniden el mi koyacak? Tahmininizi yazın!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "lyon": {
        "title_tr": "Lyon: 500M€ Borç ve Küme Düşme Emri! 😱📉 #shorts",
        "description_tr": "Fransız devi Lyon, Amerikalı sahip John Textor döneminde 500 milyon euro borçla Ligue 2'ye düşürülme kararıyla yüzleşti. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #lyon #ligue1 #sporfinansı",
        "tags_tr": ["shorts", "futbol", "lyon", "ligue 1", "john textor", "spor finansı"],
        "title_en": "Lyon: John Textor's €500M Debt & Provisional Relegation! 😱📉 #shorts #football",
        "description_en": "French football powerhouse Olympique Lyonnais has been hit with a provisional Ligue 1 relegation order over €500 million in debt under American owner John Textor.\n\nSubscribe to SportStory for daily sports business breakdowns.\n\n#shorts #football #lyon #ligue1 #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "lyon", "ligue 1", "john textor", "sports finance", "eagle football"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Olympique Lyonnais dominated French football for decades, but now they face catastrophic mandatory relegation to Ligue Two.", "text_tr": "Olympique Lyonnais yıllarca Fransız futbolunu domine etti ama şimdi Ligue 2'ye düşürülme kabusuyla karşı karşıya.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "American investor John Textor's multi-club vehicle Eagle Football piled up over five hundred million euros in crippling liabilities.", "text_tr": "Amerikalı yatırımcı John Textor'ın şirketi kulübe 500 milyon euroyu aşan felaket bir borç yükledi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "French financial watchdog DNCG handed Lyon an immediate transfer ban and provisional relegation unless finances are fixed.", "text_tr": "Fransız mali denetleme kurulu DNCG, borçlar ödenmezse Lyon'a transfer yasağı ve küme düşme cezası kesti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Now Lyon must execute emergency fire sales of top young stars to plug a hundred-million-euro black hole.", "text_tr": "Şimdi Lyon yüz milyon euroluk kara deliği kapatmak için genç yıldızlarını yok pahasına satmak zorunda.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Can multi-club ownership survive in European football, or is Lyon doomed? Let us know below!", "text_tr": "Çoklu kulüp sahipliği Avrupa futbolunda hayatta kalabilir mi yoksa Lyon mahvoldu mu? Yorumlarda buluşalım!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "parma": {
        "title_tr": "Parma: Parmalat'ın 14 Milyar Euroluk İflası! 🥛📉 #shorts",
        "description_tr": "Buffon ve Cannavaro'lu Parma Calcio'yu yok eden tarihin en büyük süt dolandırıcılığı ve iflası. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #parma #seriea #parmalat",
        "tags_tr": ["shorts", "futbol", "parma", "serie a", "parmalat", "spor finansı"],
        "title_en": "The $14B Fraud That Killed Parma Calcio! 🥛📉 #shorts #football",
        "description_en": "Parma Calcio won European trophies with Buffon and Cannavaro, but Parmalat's €14 billion corporate dairy fraud imploded overnight, sending the club into bankruptcy.\n\nSubscribe to SportStory for daily sports finance breakdowns.\n\n#shorts #football #parma #seriea #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "parma", "serie a", "parmalat", "sports finance", "buffon"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Parma Calcio won European trophies while secretly drowning in a staggering multi-billion-dollar corporate dairy fraud.", "text_tr": "Parma Calcio devasa milyarlık kurumsal süt dolandırıcılığının içinde boğulurken Avrupa kupaları kazandı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Backed by Parmalat, club owners pumped fake revenues into buying world-class superstars on lavish contracts.", "text_tr": "Parmalat destekli yönetim, sahte gelirlerle lüks sözleşmeler imzalayarak dünya klasında süper yıldızlar aldı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Then the dairy empire imploded overnight, exposing fourteen billion euros in hidden debt and catastrophic fraud.", "text_tr": "Ardından süt imparatorluğu bir gecede çökerek 14 milyar euro gizli borcu gün ışığına çıkardı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Parma suffered brutal bankruptcy, stripping their assets, forcing fire sales, and plunging into amateur divisions.", "text_tr": "Parma acımasız iflaslar yaşayarak varlıklarını kaybetti ve amatör liglere kadar çöküş yaşadı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Was Parma the greatest team destroyed by corporate greed? Drop your thoughts below!", "text_tr": "Parma açgözlülük yüzünden yok olan en büyük takım mıydı? Yorumlarda buluşalım!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "rangers": {
        "title_tr": "Rangers: 54 Şampiyonluktan 4. Lige Tasfiye! 🏴󠁧󠁢󠁳󠁣󠁴󠁿📉 #shorts",
        "description_tr": "İskoç devi Rangers FC'nin ödenmeyen vergiler yüzünden tasfiye edilip 4. lige sürgün edilişi. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #rangers #sporfinansı",
        "tags_tr": ["shorts", "futbol", "rangers", "tasfiye", "spor finansı"],
        "title_en": "How Scotland's Biggest Club Died in 2012! 🏴󠁧󠁢󠁳󠁣󠁴󠁿📉 #shorts #football",
        "description_en": "Rangers FC won 54 Scottish league titles, but catastrophic tax schemes and £24 million in unpaid debt forced total liquidation and exile to the fourth tier.\n\nSubscribe to SportStory for daily football scandals.\n\n#shorts #football #rangers #scottishfootball #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "rangers fc", "scottish premiership", "liquidation", "sports finance"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Scottish giant Rangers FC boasted fifty-four league titles before an unpaid tax scandal completely liquidated them.", "text_tr": "İskoç devi Rangers FC 54 lig şampiyonluğuna sahipti ancak ödenmeyen vergi skandalı kulübü tasfiye etti.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Secret employee benefit trusts concealed massive player salaries, evading British tax authorities for over a decade.", "text_tr": "Gizli vakıf fonları üzerinden oyuncu maaşları saklandı ve İngiliz vergi dairesinden 10 yıl gelir gizlendi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "When tax authorities issued a crushing sixty-million-pound bill, the club collapsed into financial administration.", "text_tr": "Vergi dairesi 60 milyon sterlinlik faturayı kestiğinde kulüp kayyuma ve iflasa sürüklendi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Rivals voted to banish Rangers to the fourth tier, forcing Scotland's biggest club to restart from zero.", "text_tr": "Rakipleri Rangers'ı 4. lige düşürmek için oy kullandı ve dev kulüp sıfırdan başlamak zorunda kaldı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Did Rangers pay the ultimate price, or was the punishment too harsh? Let us know below!", "text_tr": "Rangers bedelini fazlasıyla ödedi mi yoksa ceza çok mu ağırdı? Fikrini yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "portsmouth": {
        "title_tr": "Portsmouth: Kupadan İflas ve Hapse! 🚨📉 #shorts",
        "description_tr": "FA Cup zaferinden 4. lige çöküşe: 135 milyon sterlinlik borç, hapse giren kulüp sahipleri ve iflas. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #portsmouth #premierleague #skandal",
        "tags_tr": ["shorts", "futbol", "portsmouth", "premier lig", "fa cup", "spor finansı"],
        "title_en": "From FA Cup Winners To Total Liquidation! 🚨📉 #shorts #football",
        "description_en": "In 2008, Portsmouth won the FA Cup. Two years later, £135 million in reckless debt and fraud led to administration, relegation, and owners going to prison.\n\nSubscribe to SportStory for daily sports finance.\n\n#shorts #football #portsmouth #premierleague #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "portsmouth", "premier league", "fa cup", "sports finance", "scandal"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Portsmouth won the FA Cup and played AC Milan, but reckless spending brought catastrophic bankruptcy.", "text_tr": "Portsmouth FA Cup kazandı ve Milan'la oynadı ama kontrolsüz harcamalar felaket bir iflas getirdi.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Four different mysterious foreign owners took over in one single season, piling up unpaid player wages.", "text_tr": "Tek bir sezonda 4 farklı gizemli yabancı sahip geldi ve ödenmeyen maaşlar dağ gibi birikti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Debts rocketed past one hundred and thirty-five million pounds, triggering a nine-point penalty and relegation.", "text_tr": "Borç 135 milyon sterlini aştı, kulübe 9 puan silme cezası verildi ve küme düştü.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Executive fraud lawsuits sent owners to prison while Portsmouth crashed into English football's fourth division.", "text_tr": "Dolandırıcılık davaları sahipleri hapse yollarken Portsmouth İngiliz 4. ligine kadar çakıldı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Is Portsmouth the worst-run club in Premier League history? Share your verdict below!", "text_tr": "Portsmouth Premier Lig tarihinin en kötü yönetilen kulübü müydü? Yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "valencia": {
        "title_tr": "Valencia: Hayalet Stadyum ve Peter Lim! 👻🚨 #shorts",
        "description_tr": "Valencia Şampiyonlar Ligi finallerinden küme düşme hattına: 15 yıldır çürüyen Nou Mestalla inşaatı. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #valencia #laliga #peterlim",
        "tags_tr": ["shorts", "futbol", "valencia", "la liga", "peter lim", "nou mestalla", "spor finansı"],
        "title_en": "Valencia: The Ghost Stadium & Peter Lim's Ruin! 👻🚨 #shorts #football",
        "description_en": "How Valencia went from Champions League finals to fighting relegation under billionaire Peter Lim, with an abandoned half-built stadium left rotting for 15 years.\n\nSubscribe to SportStory for daily football scandals.\n\n#shorts #football #valencia #laliga #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "valencia", "la liga", "peter lim", "nou mestalla", "sports finance"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Valencia played back-to-back Champions League finals, but a half-built concrete skeleton stadium doomed their future.", "text_tr": "Valencia üst üste Şampiyonlar Ligi finali oynadı ancak yarım kalan hayalet stadyum geleceklerini kararttı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Construction on the Nou Mestalla halted in 2009 when real estate loans completely collapsed during Spain's crisis.", "text_tr": "Nou Mestalla inşaatı, İspanya'daki krizde emlak kredileri batınca 2009'da tamamen durdu.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Singaporean billionaire Peter Lim bought the club, promising a completed stadium and world-class glory.", "text_tr": "Singapurlu milyarder Peter Lim kulübü satın aldı ve stadyumu bitirip dünya devliği vadetti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Instead, Lim sold captain Parejo for pennies, fired top managers, and left the stadium rotting.", "text_tr": "Bunun yerine kaptan Parejo'yu bedavaya sattı, hocaları kovdu ve stadyumu çürümeye terk etti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Can Valencia ever escape Peter Lim, or is historic relegation next? Comment below!", "text_tr": "Valencia Peter Lim'den kurtulabilir mi yoksa küme mi düşecekler? Fikrini yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "psg": {
        "title_tr": "PSG: 1.5 Milyar Euroluk UEFA Hile Çarkı! 💸🚨 #shorts",
        "description_tr": "Paris Saint-Germain Neymar ve Mbappe'ye milyarlar akıtırken UEFA FFP cezalarını nasıl atlattı? 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #psg #uefa #sporfinansı",
        "tags_tr": ["shorts", "futbol", "psg", "neymar", "mbappe", "uefa ffp", "spor finansı"],
        "title_en": "How PSG Spent $1.5B To Hide UEFA Sanctions! 💸🚨 #shorts #football",
        "description_en": "Paris Saint-Germain spent billions in Qatari funds on Neymar and Mbappe, yet secretly piled up massive losses and UEFA financial fair play probes.\n\nSubscribe to SportStory for sports business analysis.\n\n#shorts #football #psg #uefa #sportsfinance",
        "tags_en": ["shorts", "football", "soccer", "psg", "qsi", "neymar", "mbappe", "uefa ffp", "sports finance"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Paris Saint-Germain spent over one billion euros, smashing world transfer records while evading UEFA penalties.", "text_tr": "Paris Saint-Germain UEFA cezalarından kaçarken 1 milyar eurodan fazla harcayıp transfer rekorlarını kırdı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Inflated state sponsorship deals from Qatar funded astronomical contracts for Neymar, Messi, and Kylian Mbappe.", "text_tr": "Katar'dan gelen şişirilmiş sponsorluklar Neymar, Messi ve Mbappe'nin astronomik maaşlarını fonladı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Behind the scenes, French police probed secret tax exemptions granted to facilitate Neymar's world-record move.", "text_tr": "Arka planda Fransız polisi Neymar'ın rekor transferini kolaylaştıran gizli vergi muafiyetlerini araştırdı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "When Mbappe walked away for free to Real Madrid, PSG was left with massive annual operating losses.", "text_tr": "Mbappe bedavaya Real Madrid'e gittiğinde PSG devasa yıllık işletme zararlarıyla baş başa kaldı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Did state-backed billions ruin modern football or make it more entertaining? Drop your thoughts below!", "text_tr": "Devlet destekli milyarlar modern futbolu mahvetti mi yoksa güzelleştirdi mi? Yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "schwarz": {
        "title_tr": "Uzaya Gitmesi Yasaklanan Futbolcu! 🚀⚽ #shorts",
        "description_tr": "Stefan Schwarz ve spor tarihinin en inanılmaz sözleşme maddesi: Uzaya seyahat yasağı! 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #stefanschwarz #sözleşme #absürt #premierleague",
        "tags_tr": ["shorts", "futbol", "stefan schwarz", "absürt sözleşmeler", "sunderland", "premier lig", "uzay", "ilginç maddeler"],
        "title_en": "The Bizarre Space Ban Contract! 🚀⚽ #shorts",
        "description_en": "In 1999, Sunderland legally banned Swedish international Stefan Schwarz from traveling to outer space! 🔔 Subscribe to @SportStory for incredible football trivia & scandals. #shorts #football #soccer #stefanschwarz #contracts",
        "tags_en": ["shorts", "football", "soccer", "stefan schwarz", "bizarre contracts", "sunderland", "premier league", "space clause"],
        "scenes": [
            {"scene_idx": 1, "text_en": "In 1999, Sunderland signed Swedish star Stefan Schwarz with one of the most insane clauses in sports history.", "text_tr": "1999'da Sunderland, İsveçli yıldız Stefan Schwarz ile spor tarihinin en çılgın sözleşmesine imza attı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Schwarz was fascinated by space travel and publicly expressed a desire to book the world's first commercial flight to space.", "text_tr": "Schwarz uzay yolculuğuna meraklıydı ve ilk ticari uzay uçuşuna bilet alma arzusunu açıklamıştı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Terrified of losing their star to orbit, Sunderland legally banned him from traveling to outer space during his contract.", "text_tr": "Yıldızını uzay boşluğuna kaptırmaktan korkan Sunderland, sözleşmeye oyuncunun uzaya çıkmasını yasaklayan resmi bir madde koydu.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "If Schwarz boarded a spacecraft or rocket before 2004, his multi-million-pound contract would be terminated instantly.", "text_tr": "Eğer Schwarz 2004'ten önce bir uzay aracına binerse milyonluk sözleşmesi anında feshedilecekti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Is this the most ridiculous clause ever written into a football contract? Share your thoughts below!", "text_tr": "Bu bir futbol sözleşmesine yazılmış en absürt madde mi? Yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "ronaldo": {
        "title_tr": "Ronaldo: Saniyede 7$ Kazanan Makine! 💸⌛ #shorts",
        "description_tr": "Cristiano Ronaldo Al Nassr'da saniyede 7 dolar, uykusunda 38 bin dolar kazanıyor! 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #ronaldo #alnassr #servet #maaş",
        "tags_tr": ["shorts", "futbol", "cristiano ronaldo", "ronaldo", "al nassr", "maaş", "servet", "para"],
        "title_en": "Ronaldo: The $7 Per Second Machine! 💸⌛ #shorts",
        "description_en": "Cristiano Ronaldo earns €200M every single year at Al Nassr. That breaks down to $7 every second of the day! 🔔 Subscribe to @SportStory for daily football wealth breakdowns. #shorts #football #ronaldo #cr7 #salary",
        "tags_en": ["shorts", "football", "soccer", "cristiano ronaldo", "ronaldo", "cr7", "al nassr", "sports finance", "salary"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Cristiano Ronaldo earns an astronomical two hundred million euros every single year at Saudi club Al Nassr.", "text_tr": "Cristiano Ronaldo, Suudi kulübü Al Nassr'da yılda tam iki yüz milyon euro kazanıyor.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "That breaks down to nearly seventeen million euros a month, or an unbelievable six hundred thousand euros every day.", "text_tr": "Bu ayda yaklaşık on yedi milyon euroya, yani günde inanılmaz altı yüz bin euroya denk geliyor.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "While you are watching this short, Ronaldo effortlessly generates seven dollars every single second of the clock.", "text_tr": "Siz bu videoyu izlerken Ronaldo her saniye saat gibi cebine tam yedi dolar koyuyor.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Even during nine hours of sleep, his bank account automatically inflates by over thirty-eight thousand dollars.", "text_tr": "Gece dokuz saatlik uykusunda bile banka hesabı kendiliğinden tam otuz sekiz bin dolar şişiyor.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Does any athlete on planet Earth truly deserve this level of wealth? Drop your honest verdict!", "text_tr": "Dünya üzerinde herhangi bir sporcu bu seviyede bir serveti hak ediyor mu? Fikrini yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "bergkamp": {
        "title_tr": "Bergkamp: Uçamayan Hollandalı Maddesi! ✈️❌ #shorts",
        "description_tr": "Arsenal efsanesi Dennis Bergkamp'ın uçak korkusu ve sözleşmesindeki uçuş yasağı maddesi. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #bergkamp #arsenal #premierleague",
        "tags_tr": ["shorts", "futbol", "dennis bergkamp", "arsenal", "uçak korkusu", "premier lig", "ilginç hikayeler"],
        "title_en": "Bergkamp: The Non-Flying Clause! ✈️❌ #shorts",
        "description_en": "Why Arsenal legend Dennis Bergkamp drove 30 hours across Europe instead of flying with teammates. 🔔 Subscribe to @SportStory for daily football trivia & stories. #shorts #football #bergkamp #arsenal",
        "tags_en": ["shorts", "football", "soccer", "dennis bergkamp", "bergkamp", "arsenal", "premier league", "trivia"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Arsenal legend Dennis Bergkamp terrorized Premier League defenses, yet possessed a paralyzing fear of boarding commercial airplanes.", "text_tr": "Arsenal efsanesi Dennis Bergkamp Premier Lig savunmalarını yıktı ancak felç edici bir uçak korkusuna sahipti.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "After a terrifying engine failure scare during the 1994 World Cup, Bergkamp vowed never to fly again.", "text_tr": "1994 Dünya Kupası'ndaki korkunç motor arızasının ardından Bergkamp bir daha asla uçağa binmeyeceğine yemin etti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "He demanded an explicit contractual clause releasing him from flying to international European Champions League away fixtures.", "text_tr": "Avrupa kupası deplasmanlarına uçakla gitme zorunluluğunu kaldıran özel bir sözleşme maddesi talep etti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "While teammates flew comfortably, Bergkamp drove across Europe by car and train for thirty hours to play.", "text_tr": "Takım arkadaşları uçakla uçarken, Bergkamp maçlara yetişmek için Avrupa'yı tren ve arabayla 30 saatte aştı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Would a modern superstar ever travel thirty hours by car to play an away match? Tell us!", "text_tr": "Günümüz süper yıldızlarından biri deplasmana arabayla 30 saat gidip oynar mıydı? Yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "neymar": {
        "title_tr": "Neymar: Suudi Sarayı ve Özel Jetler! 🛩️🏰 #shorts",
        "description_tr": "Neymar'ın Al Hilal sözleşmesindeki 25 odalı saray, özel jet ve 500 bin euroluk post primi. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #neymar #alhilal #servet",
        "tags_tr": ["shorts", "futbol", "neymar", "al hilal", "suudi arabistan", "özel jet", "transfer", "maaş"],
        "title_en": "Neymar: Private Jets & Saudi Palaces! 🛩️🏰 #shorts",
        "description_en": "Neymar's Al Hilal deal included a 25-room palace, 24/7 private jet, and €500,000 for each social media post! 🔔 Subscribe to @SportStory for sports finance stories. #shorts #football #neymar",
        "tags_en": ["shorts", "football", "soccer", "neymar", "al hilal", "saudi pro league", "private jet", "sports finance"],
        "scenes": [
            {"scene_idx": 1, "text_en": "When Neymar signed his blockbuster Saudi contract with Al Hilal, wages were only a fraction of the deal.", "text_tr": "Neymar, Al Hilal ile devasa Suudi sözleşmesini imzaladığında maaşı anlaşmanın sadece küçük bir parçasıydı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Neymar demanded a twenty-five-room luxury mansion complete with three saunas and a personal fleet of luxury supercars.", "text_tr": "Neymar yirmi beş odalı, üç saunalı lüks bir malikane ve özel süper lüks araba filosu talep etti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "His contract included a private jet available twenty-four seven for family travel, fully paid by the club.", "text_tr": "Sözleşmesinde kulüp tarafından karşılanan, ailesi için 7/24 hazır bekleyen özel bir jet yer aldı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Plus an unbelievable five hundred thousand euros bonus for every single social media post promoting Saudi tourism.", "text_tr": "Üstüne Suudi turizmini öven her bir sosyal medya paylaşımı için beş yüz bin euro bonus aldı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Are football superstar demands reaching completely absurd levels of entitlement? Share your thoughts below!", "text_tr": "Futbol yıldızlarının talepleri artık akıl almaz bir şımarıklık seviyesine mi ulaştı? Yorumlarda buluşalım!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "reina": {
        "title_tr": "Reina: Her Yıl Ücretsiz Lego Ev! 🧱🏠 #shorts",
        "description_tr": "Giuseppe Reina'nın Arminia Bielefeld sözleşmesindeki bedava ev maddesi ve kulübün Lego cevabı! 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #absürt #lego #transfer",
        "tags_tr": ["shorts", "futbol", "giuseppe reina", "lego", "arminia bielefeld", "ilginç maddeler", "sözleşme"],
        "title_en": "Reina: The Free Lego House Clause! 🧱🏠 #shorts",
        "description_en": "Giuseppe Reina demanded a new house for every year of his contract—so the club cleverly built him miniature Lego homes! 🔔 Subscribe to @SportStory for football comedy & trivia. #shorts #football",
        "tags_en": ["shorts", "football", "soccer", "giuseppe reina", "lego", "bizarre contracts", "bundesliga", "trivia"],
        "scenes": [
            {"scene_idx": 1, "text_en": "When German striker Giuseppe Reina signed for Arminia Bielefeld, he included a hilariously ambiguous contractual demand.", "text_tr": "Alman forvet Giuseppe Reina, Arminia Bielefeld'e imza atarken sözleşmesine inanılmaz komik bir madde koydurdu.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Reina demanded that the club build him a brand-new house for every single year of his contract.", "text_tr": "Reina kulübün, sözleşmesinin geçerli olduğu her yıl için kendisine yepyeni bir ev inşa etmesini şart koştu.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "However, the clever striker completely forgot to specify the size, materials, or dimensions of the promised home.", "text_tr": "Ancak uyanık forvet, vadettiği evin boyutunu, malzemesini veya metrekaresini sözleşmede belirtmeyi unuttu.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Exploiting the loophole, club executives proudly presented him with miniature houses made entirely of plastic Lego bricks.", "text_tr": "Bu açıktan yararlanan kulüp yöneticileri, ona her yıl gururla plastikten Lego evler hediye etti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Is this the funniest contract loophole outsmarting ever recorded in football history? Let us know below!", "text_tr": "Bu futbol tarihinin en komik sözleşme kurnazlığı ve golü müydü? Yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "ruddock": {
        "title_tr": "Ruddock: 99.8 Kilo ve Ağır Para Cezası! ⚖️🍔 #shorts",
        "description_tr": "Neil Ruddock ve Crystal Palace sözleşmesindeki 99.8 kilo sınırı ile kilo başına astronomik para cezası. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #ruddock #premierleague",
        "tags_tr": ["shorts", "futbol", "neil ruddock", "kilo cezası", "crystal palace", "premier lig", "ilginç hikayeler"],
        "title_en": "Ruddock: The 99.8kg Weight Clause! ⚖️🍔 #shorts",
        "description_en": "Crystal Palace fined Neil Ruddock 10% of his wages every time he exceeded 99.8kg on the scale! 🔔 Subscribe to @SportStory for daily football stories. #shorts #football #ruddock",
        "tags_en": ["shorts", "football", "soccer", "neil ruddock", "weight clause", "crystal palace", "premier league"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Hard-tackling defender Neil Ruddock was notorious for his immense talent, heavy drinking, and uncontrollable love of junk food.", "text_tr": "Sert savunmacı Neil Ruddock yeteneği kadar kontrolsüz abur cubur aşkı ve kilolarıyla ünlüydü.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "When Crystal Palace signed him in 2000, chairman Harry Redknapp inserted a strict ninety-nine-point-eight kilogram weight cap clause.", "text_tr": "Crystal Palace 2000'de ona imza attırırken sözleşmesine katı bir 99.8 kilo sınırı maddesi ekletti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "For every single weigh-in where Ruddock exceeded the limit, he was fined a massive ten percent of his salary.", "text_tr": "Ruddock'ın bu kilo sınırını aştığı her tartı gününde maaşının tam yüzde onu ceza olarak kesildi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Ruddock was weighed eight times in his first season, paying thousands in fines while struggling to fit his shorts.", "text_tr": "İlk sezonunda sekiz kez tartıldı, formasının içine sığmaya çalışırken binlerce sterlin ceza ödedi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Should modern clubs dock player wages for being overweight, or is that too harsh? Comment below!", "text_tr": "Modern kulüpler kilo alan oyuncuların maaşını kesmeli mi yoksa bu çok mu sert? Yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "ali dia": {
        "title_tr": "Ali Dia: Premier Lig'i Dolandıran Sahte Futbolcu! 🎭🚨 #shorts",
        "description_tr": "Kendisini George Weah'ın kuzeni olarak tanıtıp Premier Lig'de forma giyen Ali Dia'nın akıl almaz hikayesi. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #alidia #premierleague #dolandırıcı",
        "tags_tr": ["shorts", "futbol", "ali dia", "sahte futbolcu", "southampton", "premier lig", "skandal", "george weah"],
        "title_en": "Ali Dia: The 53-Minute Premier League Con! 🎭🚨 #shorts",
        "description_en": "How a university student faked a phone call from George Weah to play in the Premier League for Southampton! 🔔 Subscribe to @SportStory for football scandals. #shorts #football #alidia",
        "tags_en": ["shorts", "football", "soccer", "ali dia", "premier league", "con artist", "southampton", "scandal"],
        "scenes": [
            {"scene_idx": 1, "text_en": "In 1996, Southampton manager Graeme Souness received a phone call claiming to be world superstar George Weah.", "text_tr": "1996'da Southampton menajeri Graeme Souness, kendisini dünya yıldızı George Weah olarak tanıtan bir telefon aldı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "The caller recommended his alleged cousin, Ali Dia, claiming he played for Paris Saint-Germain and Senegal.", "text_tr": "Arayan kişi Paris Saint-Germain'de oynadığını iddia ettiği kuzeni Ali Dia'yı önerdi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "In reality, it was a university student friend executing the most audacious con in Premier League history.", "text_tr": "Aslında bu Premier Lig tarihinin en cüretkar dolandırıcılığını yapan bir üniversite öğrencisiydi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Dia signed, came on as a substitute against Leeds, played horribly for fifty-three minutes, and vanished forever.", "text_tr": "Dia sözleşmeyi imzaladı, Leeds maçında 53 dakika rezil bir futbol oynadı ve ertesi sabah sonsuza dek kayboldu.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "How could a Premier League club get fooled so easily without a background check? Share your verdict!", "text_tr": "Bir Premier Lig kulübü tek bir kontrol bile yapmadan nasıl böyle kandırıldı? Fikrini yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "firmino": {
        "title_tr": "Firmino: Arsenal'a Satılamaz Maddesi! 🚫🔴 #shorts",
        "description_tr": "Liverpool'un Roberto Firmino sözleşmesine koyduğu Arsenal'a transfer yasağı maddesi! 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #firmino #liverpool #arsenal #transfer",
        "tags_tr": ["shorts", "futbol", "roberto firmino", "liverpool", "arsenal", "transfer", "premier lig"],
        "title_en": "Firmino: The Anti-Arsenal 82M Clause! 🚫🔴 #shorts",
        "description_en": "Liverpool inserted an £82M buyout clause in Roberto Firmino's contract that was valid for any club in the world—except Arsenal! 🔔 Subscribe to @SportStory. #shorts #football",
        "tags_en": ["shorts", "football", "soccer", "roberto firmino", "firmino", "liverpool", "arsenal", "transfer clause"],
        "scenes": [
            {"scene_idx": 1, "text_en": "When Liverpool signed Roberto Firmino in 2015, they included a petty release clause aimed at their fiercest rival.", "text_tr": "Liverpool 2015'te Roberto Firmino'yu aldığında en ezeli rakibini hedef alan intikam dolu bir madde ekledi.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Two years earlier, Arsenal infamously bid forty million and one pounds to trigger Luis Suarez's release clause.", "text_tr": "İki yıl önce Arsenal, Luis Suarez'i almak için kırk milyon bir sterlin teklif ederek Liverpool'u çıldırtmıştı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Furious Liverpool owners vowed never to be humiliated by Arsenal's aggressive transfer tactics ever again.", "text_tr": "Öfkeli Liverpool yönetimi Arsenal'ın bu transfer oyunlarıyla bir daha asla küçük düşmeyeceğine yemin etti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Firmino's contract had an eighty-two-million-pound buyout valid for any European club, strictly forbidding Arsenal from ever bidding.", "text_tr": "Firmino'nun sözleşmesine tüm kulüpler için 82 milyonluk serbest kalma maddesi kondu, Arsenal ise kesin olarak yasaklandı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Was this brilliant executive pettiness or an unprofessional transfer grudge? Let us know below!", "text_tr": "Bu zekice bir intikam mıydı yoksa profesyonellik dışı bir kapris mi? Yorumlarda buluşalım!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "messi": {
        "title_tr": "Messi: Apple TV Gelir Ortaklığı ve Servet! 🍏💰 #shorts",
        "description_tr": "Lionel Messi'nin Inter Miami sözleşmesindeki Apple TV ve Adidas gelir ortaklığı imparatorluğu. 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #messi #intermiami #appletv #servet",
        "tags_tr": ["shorts", "futbol", "lionel messi", "messi", "inter miami", "apple tv", "spor finansı", "servet"],
        "title_en": "Messi: The Apple TV & MLS Revenue Empire! 🍏💰 #shorts",
        "description_en": "Lionel Messi rejected €1 Billion from Saudi Arabia for a genius equity stake in Inter Miami and Apple TV revenue shares! 🔔 Subscribe to @SportStory. #shorts #football #messi",
        "tags_en": ["shorts", "football", "soccer", "lionel messi", "messi", "inter miami", "mls", "apple tv", "sports business"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Lionel Messi rejected a one-billion-dollar Saudi package to sign an unprecedented business deal in Major League Soccer.", "text_tr": "Lionel Messi bir milyar dolarlık Suudi teklifini reddederek Amerikan liginde eşi görülmemiş bir anlaşmaya imza attı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Instead of a normal salary, Messi secured direct revenue percentages from Apple TV MLS Season Pass subscriptions.", "text_tr": "Normal bir maaş yerine Apple TV'nin MLS yayın aboneliklerinden doğrudan gelir payı hakkı elde etti.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Adidas also granted him a cut of all US jersey sales, instantly turning him into an equity stakeholder.", "text_tr": "Adidas ayrıca ABD'deki tüm forma satışlarından pay vererek Messi'yi doğrudan şirketin ortağı yaptı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Most lucrative of all, Messi was granted ownership equity in Inter Miami without paying an entry franchise fee.", "text_tr": "Hepsinden önemlisi Messi'ye hiçbir giriş bedeli ödemeden Inter Miami kulübünden ortaklık hissesi verildi.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Did Lionel Messi invent the smartest athlete contract in modern sports business? Tell us what you think!", "text_tr": "Lionel Messi modern spor dünyasının en zekice sözleşmesini mi icat etti? Fikrini yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    },
    "mbappe": {
        "title_tr": "Mbappe: Real Madrid 150M€ İmza Primi! 💰👑 #shorts",
        "description_tr": "Kylian Mbappe'nin Real Madrid'den aldığı 150 milyon euroluk imza parası ve imaj hakkı sırları! 🔔 @SportStoryTR kanalına abone olun. #shorts #futbol #mbappe #realmadrid #imzaprimi #transfer",
        "tags_tr": ["shorts", "futbol", "kylian mbappe", "mbappe", "real madrid", "imza parası", "transfer", "maaş"],
        "title_en": "Mbappe: Real Madrid's 150M Signing Secret! 💰👑 #shorts",
        "description_en": "Kylian Mbappe joined Real Madrid on a 'free' transfer—yet pocketed a record €150 million signing bonus! 🔔 Subscribe to @SportStory. #shorts #football #mbappe #realmadrid",
        "tags_en": ["shorts", "football", "soccer", "kylian mbappe", "mbappe", "real madrid", "signing bonus", "sports finance"],
        "scenes": [
            {"scene_idx": 1, "text_en": "Kylian Mbappe's move to Real Madrid was hailed as a free transfer, but the reality was vastly different.", "text_tr": "Kylian Mbappe'nin Real Madrid'e transferi bedava olarak kutlandı ancak perde arkası bambaşkaydı.", "visual_prompt": "cinematic football", "is_hook": True, "is_cta": False},
            {"scene_idx": 2, "text_en": "Because Real Madrid paid no transfer fee to PSG, Mbappe demanded a staggering one-hundred-and-fifty-million-euro signing bonus.", "text_tr": "Real Madrid PSG'ye bonservis ödemediği için Mbappe tam 150 milyon euroluk devasa bir imza parası kopardı.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 3, "text_en": "Paid out across his five-year contract, this bonus adds thirty million euros every year to his standard wages.", "text_tr": "Beş yıllık sözleşmesine yayılan bu prim normal maaşının üstüne her yıl otuz milyon euro nakit ekliyor.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 4, "text_en": "Plus, he retained eighty percent of his global image rights, a privilege denied even to Cristiano Ronaldo.", "text_tr": "Üstüne Cristiano Ronaldo'ya bile verilmeyen küresel imaj haklarının yüzde seksenini elinde tuttu.", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": False},
            {"scene_idx": 5, "text_en": "Can Real Madrid sustain this astronomical spending without wrecking their dressing room harmony? Comment below!", "text_tr": "Real Madrid soyunma odası dengesini bozmadan bu harcamayı sürdürebilir mi? Yorumlara yaz!", "visual_prompt": "cinematic football", "is_hook": False, "is_cta": True}
        ]
    }
}


class ScriptWeaverAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

    def generate_script(self, topic: str, short_id: str) -> AutoScriptPayload:
        logger.info(f"✍️ ScriptWeaver: '{topic}' için eksiksiz ve derinlikli İngilizce belgesel senaryosu yazılıyor...")

        prompt = f"""
You are a senior investigative sports finance documentary writer for the channel 'SportStory'.
Write a gripping, COMPLETE 5-scene YouTube Shorts documentary script about: "{topic}".

STRICT NARRATIVE RULES:
1. Exactly 5 scenes.
2. The story MUST BE 100% COMPLETE with a full narrative arc from start to finish.
3. Total voiceover length across all 5 scenes must be between 70 and 95 words (approx. 32-40 seconds of natural speech).
4. Each scene must contain 13 to 18 words of punchy, suspenseful, informative documentary prose.
5. NEVER write 3-5 word dummy stubs! Give real details, club names, debts, transfers, and consequences.
6. Scene 1 (The Hook): A shocking opening hook stating the club name and the financial paradox/contrast.
7. Scene 2 (The Waste/Gamble): The reckless financial move, loans, contracts, or lavish spending with specific numbers.
8. Scene 3 (The Crash): The exact moment the gamble backfired and debts exploded.
9. Scene 4 (The Consequence): Relegation, losing legends, fire sales, or points deductions.
10. Scene 5 (Climax / Provocative Question): An intense final sentence asking a question to spark debate in the comments.
11. Provide BOTH English ('text_en') and Turkish ('text_tr') narration for each scene.
12. TURKISH NARRATION RULES ('text_tr'):
    - Professional, dramatic Turkish sports documentary tone (TRT Spor / beIN Sports belgesel standardı).
    - Grammatically flawless, punchy, spoken Turkish flow (13-18 words per scene).
    - NEVER produce mechanical literal translations. Use idiomatic sports terminology.
    - Write footballer, manager and club names in their ORIGINAL standard spelling (e.g. "Stefan Schwarz", "Kylian Mbappé", "Dennis Bergkamp", "Neil Ruddock", "Manchester City"). DO NOT write ugly phonetic spellings; our autonomous engine handles speech phonetics separately.
    - Follow strict TDK rules: Use apostrophes for suffixes on proper nouns (e.g. "Schwarz'ın", "City'nin", "Real Madrid'e").
    - Always separate Turkish question particles ("düşer miydi", "mümkün mü", "olur mu").
    - Write clean dates and numbers (e.g. "1999'da", "115", "€500M", "%115").
13. 'title_en': 35 to 50 characters MAXIMUM (including emojis and #shorts). Format: "[Curiosity Hook] [Emoji] #shorts".
14. 'title_tr': 35 to 50 characters MAXIMUM in Turkish (including emojis and #shorts). Format: "[Merak Uyandıran Başlık] [Emoji] #shorts".
15. 'description_en': 3-4 sentence high-retention summary with SEO keywords, ending with: "🔔 Subscribe to @SportStory for daily football finance & scandal stories." followed by 5-6 hashtags.
16. 'description_tr': 3-4 cümlelik Türkçe SEO açıklaması, sonu: "🔔 Futbol skandalları ve kulüp krizleri için @SportStoryTR kanalına abone olun." ve 5-6 etiket.
17. 'tags_en': 15 to 20 targeted English keywords.
18. 'tags_tr': 15 to 20 targeted Turkish keywords.

CRITICAL JSON FORMATTING:
Return ONLY pure JSON. Escape all inner quotes with backslashes. Do NOT put raw unescaped newlines inside strings.

OUTPUT JSON SCHEMA:
{{
  "title_en": "Title Under 50 Chars 💸 #shorts",
  "title_tr": "50 Karakter Altı Türkçe Başlık 💸 #shorts",
  "description_en": "Summary text here. 🔔 Subscribe to @SportStory for daily football finance & scandal stories. #shorts #football",
  "description_tr": "Türkçe özet. 🔔 Futbol skandalları ve kulüp krizleri için @SportStoryTR kanalına abone olun. #shorts #futbol",
  "tags_en": ["shorts", "football", "soccer", "sports finance", "football scandal"],
  "tags_tr": ["shorts", "futbol", "spor", "spor finansı", "transfer", "skandal"],
  "scenes": [
    {{
      "scene_idx": 1,
      "text_en": "English spoken voiceover (13-18 words)",
      "text_tr": "Turkish spoken voiceover",
      "visual_prompt": "cinematic football",
      "is_hook": true,
      "is_cta": false
    }},
    {{
      "scene_idx": 2,
      "text_en": "English spoken voiceover (13-18 words)",
      "text_tr": "Turkish spoken voiceover",
      "visual_prompt": "cinematic football",
      "is_hook": false,
      "is_cta": false
    }},
    {{
      "scene_idx": 3,
      "text_en": "English spoken voiceover (13-18 words)",
      "text_tr": "Turkish spoken voiceover",
      "visual_prompt": "cinematic football",
      "is_hook": false,
      "is_cta": false
    }},
    {{
      "scene_idx": 4,
      "text_en": "English spoken voiceover (13-18 words)",
      "text_tr": "Turkish spoken voiceover",
      "visual_prompt": "cinematic football",
      "is_hook": false,
      "is_cta": false
    }},
    {{
      "scene_idx": 5,
      "text_en": "English spoken voiceover (13-18 words)",
      "text_tr": "Turkish spoken voiceover",
      "visual_prompt": "cinematic football",
      "is_hook": false,
      "is_cta": true
    }}
  ]
}}
"""
        models_to_try = ["gemini-flash-lite-latest", "gemini-3.5-flash"]
        for model in models_to_try:
            if not self.api_key or self.api_key == "your_gemini_api_key_here":
                break
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, headers={"Content-Type": "application/json"}, timeout=25)
                if res.status_code == 200:
                    raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    data = parse_json_robustly(raw_text)
                    scenes = [AutoScenePlan(**s) for s in data.get("scenes", [])]
                    
                    total_words = sum(len(s.text_en.split()) for s in scenes)
                    if len(scenes) == 5 and total_words >= 55:
                        logger.info(f"✅ Gemini ({model}) ile 5 sahneli eksiksiz hikaye üretildi ({total_words} kelime)!")
                        payload = AutoScriptPayload(id=short_id, topic=topic, scenes=scenes)
                        payload.title_en = data.get("title_en")
                        payload.description_en = data.get("description_en")
                        payload.tags_en = data.get("tags_en")
                        payload.title_tr = data.get("title_tr")
                        payload.description_tr = data.get("description_tr")
                        payload.tags_tr = data.get("tags_tr")
                        return payload
                    else:
                        logger.warning(f"Gemini çıktısı çok kısa veya eksik ({total_words} kelime), alternatif aranıyor.")
            except Exception as e:
                logger.warning(f"Gemini {model} çağrısında hata: {e}")

        # Fallback to rich curated knowledge base
        return self._create_curated_fallback_script(topic, short_id)

    def _create_curated_fallback_script(self, topic: str, short_id: str) -> AutoScriptPayload:
        topic_lower = topic.lower()
        matched_key = None

        # 1. Konu içinde eşleşen bir kulüp var mı?
        for key in MASTER_KNOWLEDGE_FALLBACKS.keys():
            if key in topic_lower or (key == "milan" and "ac milan" in topic_lower):
                matched_key = key
                break

        # 2. Eğer eşleşen kulüp yoksa, asla rastgele kulüp atayıp başlık-konu uyumsuzluğu yaratma!
        # ContentGuard soğuma süresine bakarak henüz kullanılmamış bir fallback seç ve konuyu o kulüple güncelle!
        if not matched_key:
            from engine.guards.content_guard import get_content_guard
            guard = get_content_guard()
            available_keys = [k for k in MASTER_KNOWLEDGE_FALLBACKS.keys() if not guard.is_club_on_cooldown(k, cooldown_count=6)[0]]
            matched_key = random.choice(available_keys) if available_keys else random.choice(list(MASTER_KNOWLEDGE_FALLBACKS.keys()))
            club_title = matched_key.title()
            topic = f"{club_title}: Untold Financial Collapse & Scandals"
            logger.warning(f"⚠️ Konu doğrudan eşleşmedi. Uyumsuzluğu önlemek için güvenli yedek '{club_title}' konusuna geçildi.")

        data = MASTER_KNOWLEDGE_FALLBACKS[matched_key]
        scenes = [AutoScenePlan(**s) for s in data["scenes"]]
        payload = AutoScriptPayload(id=short_id, topic=topic, scenes=scenes)
        payload.title_en = data["title_en"]
        payload.description_en = data["description_en"]
        payload.tags_en = data["tags_en"]
        payload.title_tr = data.get("title_tr")
        payload.description_tr = data.get("description_tr")
        payload.tags_tr = data.get("tags_tr")
        return payload
