"""Add GPC translation fields to experience translations

Revision ID: f8a9b0c1d2e3
Revises: a7241db3ee6a
Create Date: 2025-12-15 12:00:00.000000

This migration adds 5 GPC (Global Privacy Control) translatable fields to the
ExperienceTranslation and PrivacyExperienceConfigHistory tables:
- gpc_label: "Global Privacy Control"
- gpc_description: Description shown when GPC preference is honored
- gpc_status_applied_label: "Applied"
- gpc_status_overridden_label: "Overridden"
- gpc_title: "Global Privacy Control detected"

These fields allow customization of GPC-related strings that were previously
static in FidesJS locale files.
"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "f8a9b0c1d2e3"
down_revision = "a7241db3ee6a"
branch_labels = None
depends_on = None

# GPC translations for all supported languages (from FidesJS static messages)
# fmt: off
GPC_TRANSLATIONS = {
    "ar": {
        "gpc_label": "التحكم في الخصوصية العالمية",
        "gpc_description": "تم احترام تفضيلك للتحكم في الخصوصية العالمية. لقد تم إلغاء اشتراكك تلقائيًا من حالات استخدام البيانات التي تلتزم بالتحكم في الخصوصية العالمية.",
        "gpc_status_applied_label": "مُطبَّق",
        "gpc_status_overridden_label": "تم تجاوزه",
        "gpc_title": "تم الكشف عن التحكم في الخصوصية العالمية",
    },
    "bg": {
        "gpc_label": "Глобален контрол на поверителността",
        "gpc_description": "Вашите глобални предпочитания за контрол на поверителността бяха уважени. Бяхте автоматично изключени от случаите на използване на данни, които се придържат към глобалния контрол на поверителността.",
        "gpc_status_applied_label": "Приложено",
        "gpc_status_overridden_label": "Отменено",
        "gpc_title": "Открит глобален контрол на поверителността",
    },
    "bs": {
        "gpc_label": "Globalna kontrola privatnosti",
        "gpc_description": "Vaša globalna postavka privatnosti je poštovana. Automatski ste isključeni iz slučajeva korištenja podataka koji se pridržavaju globalne kontrole privatnosti.",
        "gpc_status_applied_label": "Primijenjeno",
        "gpc_status_overridden_label": "Poništeno",
        "gpc_title": "Otkrivena globalna kontrola privatnosti",
    },
    "ca": {
        "gpc_label": "Control de privadesa global",
        "gpc_description": "S'ha respectat la vostra preferència de control de privadesa global. Se us ha exclòs automàticament dels casos d'ús de dades que s'adhereixen al control de privadesa global.",
        "gpc_status_applied_label": "Aplicat",
        "gpc_status_overridden_label": "Anul·lat",
        "gpc_title": "Control de privadesa global detectat",
    },
    "cs": {
        "gpc_label": "Globální kontrola soukromí",
        "gpc_description": "Vaše preference globální kontroly soukromí byla respektována. Byli jste automaticky odhlášeni z případů používání dat, které se řídí globální kontrolou soukromí.",
        "gpc_status_applied_label": "Použito",
        "gpc_status_overridden_label": "Přepsáno",
        "gpc_title": "Detekována globální kontrola soukromí",
    },
    "da": {
        "gpc_label": "Global privatlivskontrol",
        "gpc_description": "Din globale privatlivskontrolpræference er blevet respekteret. Du er automatisk blevet frameldt databrugssituationer, der overholder global privatlivskontrol.",
        "gpc_status_applied_label": "Anvendt",
        "gpc_status_overridden_label": "Tilsidesat",
        "gpc_title": "Global privatlivskontrol registreret",
    },
    "de": {
        "gpc_label": "Globale Datenschutzeinstellungen",
        "gpc_description": "Ihre globale Datenschutzeinstellungen werden berücksichtigt. Sie wurden automatisch von Anwendungsfällen ausgenommen, die nicht Ihren globalen Datenschutzeinstellungen unterliegen.",
        "gpc_status_applied_label": "Angewendet",
        "gpc_status_overridden_label": "Überschrieben",
        "gpc_title": "Globale Datenschutzkontrolle erkannt",
    },
    "el": {
        "gpc_label": "Καθολικός έλεγχος απορρήτου",
        "gpc_description": "Η προτίμησή σας για τον καθολικό έλεγχο απορρήτου έχει τηρηθεί. Έχετε εξαιρεθεί αυτόματα από περιπτώσεις χρήσης δεδομένων που συμμορφώνονται με τον καθολικό έλεγχο απορρήτου.",
        "gpc_status_applied_label": "Εφαρμόστηκε",
        "gpc_status_overridden_label": "Παρακάμφθηκε",
        "gpc_title": "Εντοπίστηκε ο καθολικός έλεγχος απορρήτου",
    },
    "en": {
        "gpc_label": "Global Privacy Control",
        "gpc_description": "Your global privacy control preference has been honored. You have been automatically opted out of data use cases which adhere to global privacy control.",
        "gpc_status_applied_label": "Applied",
        "gpc_status_overridden_label": "Overridden",
        "gpc_title": "Global Privacy Control detected",
    },
    "es": {
        "gpc_label": "Control de privacidad global",
        "gpc_description": "Su preferencia de control de privacidad global se ha respetado. Se le ha excluido automáticamente de los casos de uso de datos que se adhieren al control de privacidad global.",
        "gpc_status_applied_label": "Aplicado",
        "gpc_status_overridden_label": "Anulado",
        "gpc_title": "Control de privacidad global detectado",
    },
    "es-MX": {
        "gpc_label": "Control de Privacidad Global",
        "gpc_description": "Se ha respetado su preferencia de control de privacidad global. Ha sido automáticamente excluido de los casos de uso de datos que se adhieren al control de privacidad global.",
        "gpc_status_applied_label": "Aplicado",
        "gpc_status_overridden_label": "Anulado",
        "gpc_title": "Control de privacidad global detectado",
    },
    "et": {
        "gpc_label": "Üldine privaatsuskontroll",
        "gpc_description": "Teie üldist privaatsuskontrolli eelistust on austatud. Teid on automaatselt välja arvatud andmekasutuse juhtudest, mis järgivad üldist privaatsuskontrolli.",
        "gpc_status_applied_label": "Rakendatud",
        "gpc_status_overridden_label": "Tühistatud",
        "gpc_title": "Üldine privaatsuskontroll tuvastatud",
    },
    "eu": {
        "gpc_label": "Pribatutasun kontrola orokorra",
        "gpc_description": "Zure pribatutasun kontrol orokorraren hobespenak errespetatu dira. Automatikoki atera zaituzte pribatutasun kontrol orokorrari atxikitzen zaizkion datuen erabilerako kasuetatik.",
        "gpc_status_applied_label": "Aplikatuta",
        "gpc_status_overridden_label": "Gainidatzia",
        "gpc_title": "Pribatutasun kontrol orokorra detektatua",
    },
    "fi": {
        "gpc_label": "Yleinen yksityisyyden hallinta",
        "gpc_description": "Yleinen yksityisyyden hallintavalintasi on otettu huomioon. Sinut on automaattisesti poistettu datankäyttötapauksista, jotka noudattavat yleistä yksityisyyden hallintaa.",
        "gpc_status_applied_label": "Sovellettu",
        "gpc_status_overridden_label": "Ohitettu",
        "gpc_title": "Yleinen yksityisyyden hallinta havaittu",
    },
    "fr": {
        "gpc_label": "Global Privacy Control",
        "gpc_description": "Votre préférence en matière de contrôle global de la confidentialité (GPC) a été respectée. Vous avez automatiquement été retiré des cas d'usage des données qui adhèrent au GPC.",
        "gpc_status_applied_label": "Appliqué",
        "gpc_status_overridden_label": "Ignoré",
        "gpc_title": "Contrôle global de la confidentialité détecté",
    },
    "fr-CA": {
        "gpc_label": "Contrôle global de la confidentialité",
        "gpc_description": "Votre préférence de contrôle global de la confidentialité a été respectée. Vous avez été automatiquement retiré des cas d'utilisation de données qui adhèrent au contrôle global de la confidentialité.",
        "gpc_status_applied_label": "Appliqué",
        "gpc_status_overridden_label": "Annulé",
        "gpc_title": "Contrôle global de la confidentialité détecté",
    },
    "gl": {
        "gpc_label": "Control de privacidade global",
        "gpc_description": "A súa preferencia de control de privacidade global foi respectada. Foi excluído automaticamente dos casos de uso de datos que se adhiren ao control de privacidade global.",
        "gpc_status_applied_label": "Aplicado",
        "gpc_status_overridden_label": "Anulado",
        "gpc_title": "Control de privacidade global detectado",
    },
    "hi-IN": {
        "gpc_label": "वैश्विक गोपनीयता नियंत्रण",
        "gpc_description": "आपकी वैश्विक गोपनीयता नियंत्रण प्राथमिकता का सम्मान किया गया है। आपको स्वचालित रूप से उन डेटा उपयोग मामलों से बाहर कर दिया गया है जो वैश्विक गोपनीयता नियंत्रण का पालन करते हैं।",
        "gpc_status_applied_label": "लागू",
        "gpc_status_overridden_label": "ओवरराइड",
        "gpc_title": "वैश्विक गोपनीयता नियंत्रण पाया गया",
    },
    "hr": {
        "gpc_label": "Globalna kontrola privatnosti",
        "gpc_description": "Vaša globalna postavka privatnosti je poštovana. Automatski ste isključeni iz slučajeva korištenja podataka koji se pridržavaju globalne kontrole privatnosti.",
        "gpc_status_applied_label": "Primijenjeno",
        "gpc_status_overridden_label": "Poništeno",
        "gpc_title": "Otkrivena globalna kontrola privatnosti",
    },
    "hu": {
        "gpc_label": "Globális adatvédelmi ellenőrzés",
        "gpc_description": "A globális adatvédelmi ellenőrzési beállítása tiszteletben lett tartva. Automatikusan le lett iratkoztatva azokról az adatfelhasználási esetekről, amelyek megfelelnek a globális adatvédelmi ellenőrzésnek.",
        "gpc_status_applied_label": "Alkalmazva",
        "gpc_status_overridden_label": "Felülírva",
        "gpc_title": "Globális adatvédelmi ellenőrzés észlelve",
    },
    "it": {
        "gpc_label": "Controllo Globale della Privacy",
        "gpc_description": "La tua preferenza di Controllo Globale della Privacy è stata rispettata. Sei stato automaticamente escluso dai casi d'uso dei dati che aderiscono al Controllo Globale della Privacy.",
        "gpc_status_applied_label": "Applicato",
        "gpc_status_overridden_label": "Sovrascritto",
        "gpc_title": "Controllo Globale della Privacy rilevato",
    },
    "ja": {
        "gpc_label": "グローバルプライバシーコントロール",
        "gpc_description": "グローバルプライバシーコントロールの設定が適用されました。グローバルプライバシーコントロールに準拠するデータ利用ケースから自動的にオプトアウトされました。",
        "gpc_status_applied_label": "適用済み",
        "gpc_status_overridden_label": "オーバーライド",
        "gpc_title": "グローバルプライバシーコントロールが検出されました",
    },
    "lt": {
        "gpc_label": "Visuotinė privatumo kontrolė",
        "gpc_description": "Jūsų visuotinės privatumo kontrolės nuostatos buvo paisomos. Jūs buvote automatiškai atsisakyti duomenų naudojimo atvejų, kurie atitinka visuotinę privatumo kontrolę.",
        "gpc_status_applied_label": "Pritaikyta",
        "gpc_status_overridden_label": "Nepaisyta",
        "gpc_title": "Aptikta visuotinė privatumo kontrolė",
    },
    "lv": {
        "gpc_label": "Globālā privātuma kontrole",
        "gpc_description": "Jūsu globālā privātuma kontroles preference ir ievērota. Jūs esat automātiski izslēgts no datu izmantošanas gadījumiem, kas ievēro globālo privātuma kontroli.",
        "gpc_status_applied_label": "Piemērots",
        "gpc_status_overridden_label": "Ignorēts",
        "gpc_title": "Konstatēta globālā privātuma kontrole",
    },
    "mt": {
        "gpc_label": "Kontroll Globali tal-Privatezza",
        "gpc_description": "Il-preferenza tiegħek tal-kontroll globali tal-privatezza ġiet rispettata. Int ġejt awtomatikament eskluż/a minn każijiet ta' użu ta' data li jaderixxi mal-kontroll globali tal-privatezza.",
        "gpc_status_applied_label": "Applikat",
        "gpc_status_overridden_label": "Injorat",
        "gpc_title": "Kontroll globali tal-privatezza misjub",
    },
    "nl": {
        "gpc_label": "Global Privacy Control",
        "gpc_description": "Uw Global Privacy Control-voorkeur is gerespecteerd. U bent automatisch afgemeld voor gegevensverwerkingsgevallen die voldoen aan Global Privacy Control.",
        "gpc_status_applied_label": "Toegepast",
        "gpc_status_overridden_label": "Overschreven",
        "gpc_title": "Global Privacy Control gedetecteerd",
    },
    "no": {
        "gpc_label": "Global personvernkontroll",
        "gpc_description": "Din globale personvernkontrollpreferanse har blitt respektert. Du har automatisk blitt meldt av datausetilfeller som følger global personvernkontroll.",
        "gpc_status_applied_label": "Anvendt",
        "gpc_status_overridden_label": "Overstyrt",
        "gpc_title": "Global personvernkontroll oppdaget",
    },
    "pl": {
        "gpc_label": "Globalna kontrola prywatności",
        "gpc_description": "Twoje preferencje globalnej kontroli prywatności zostały uszanowane. Zostałeś automatycznie wypisany z przypadków wykorzystania danych, które przestrzegają globalnej kontroli prywatności.",
        "gpc_status_applied_label": "Zastosowano",
        "gpc_status_overridden_label": "Nadpisano",
        "gpc_title": "Wykryto globalną kontrolę prywatności",
    },
    "pt-BR": {
        "gpc_label": "Controle Global de Privacidade",
        "gpc_description": "Sua preferência de Controle Global de Privacidade foi respeitada. Você foi automaticamente excluído dos casos de uso de dados que aderem ao Controle Global de Privacidade.",
        "gpc_status_applied_label": "Aplicado",
        "gpc_status_overridden_label": "Substituído",
        "gpc_title": "Controle Global de Privacidade detectado",
    },
    "pt-PT": {
        "gpc_label": "Controlo Global de Privacidade",
        "gpc_description": "A sua preferência de Controlo Global de Privacidade foi respeitada. Foi automaticamente excluído dos casos de utilização de dados que aderem ao Controlo Global de Privacidade.",
        "gpc_status_applied_label": "Aplicado",
        "gpc_status_overridden_label": "Substituído",
        "gpc_title": "Controlo Global de Privacidade detetado",
    },
    "ro": {
        "gpc_label": "Control global al confidențialității",
        "gpc_description": "Preferința dvs. de control global al confidențialității a fost respectată. Ați fost automat exclus din cazurile de utilizare a datelor care aderă la controlul global al confidențialității.",
        "gpc_status_applied_label": "Aplicat",
        "gpc_status_overridden_label": "Anulat",
        "gpc_title": "Control global al confidențialității detectat",
    },
    "ru": {
        "gpc_label": "Глобальный контроль конфиденциальности",
        "gpc_description": "Ваши глобальные настройки конфиденциальности были учтены. Вы были автоматически исключены из случаев использования данных, которые соответствуют глобальному контролю конфиденциальности.",
        "gpc_status_applied_label": "Применено",
        "gpc_status_overridden_label": "Переопределено",
        "gpc_title": "Обнаружен глобальный контроль конфиденциальности",
    },
    "sk": {
        "gpc_label": "Globálna kontrola súkromia",
        "gpc_description": "Vaša preferencia globálnej kontroly súkromia bola rešpektovaná. Boli ste automaticky odhlásení z prípadov použitia údajov, ktoré sa riadia globálnou kontrolou súkromia.",
        "gpc_status_applied_label": "Použité",
        "gpc_status_overridden_label": "Prepísané",
        "gpc_title": "Zistená globálna kontrola súkromia",
    },
    "sl": {
        "gpc_label": "Globalni nadzor zasebnosti",
        "gpc_description": "Vaša nastavitev globalnega nadzora zasebnosti je bila upoštevana. Samodejno ste bili izključeni iz primerov uporabe podatkov, ki se držijo globalnega nadzora zasebnosti.",
        "gpc_status_applied_label": "Uporabljeno",
        "gpc_status_overridden_label": "Preglaseno",
        "gpc_title": "Zaznan globalni nadzor zasebnosti",
    },
    "sr-Cyrl": {
        "gpc_label": "Глобална контрола приватности",
        "gpc_description": "Ваша поставка глобалне контроле приватности је поштована. Аутоматски сте искључени из случајева употребе података који се придржавају глобалне контроле приватности.",
        "gpc_status_applied_label": "Примењено",
        "gpc_status_overridden_label": "Поништено",
        "gpc_title": "Откривена глобална контрола приватности",
    },
    "sr-Latn": {
        "gpc_label": "Globalna kontrola privatnosti",
        "gpc_description": "Vaša postavka globalne kontrole privatnosti je poštovana. Automatski ste isključeni iz slučajeva upotrebe podataka koji se pridržavaju globalne kontrole privatnosti.",
        "gpc_status_applied_label": "Primenjeno",
        "gpc_status_overridden_label": "Poništeno",
        "gpc_title": "Otkrivena globalna kontrola privatnosti",
    },
    "sv": {
        "gpc_label": "Global sekretesskontroll",
        "gpc_description": "Din globala sekretesskontrollinställning har respekterats. Du har automatiskt avregistrerats från dataanvändningsfall som följer global sekretesskontroll.",
        "gpc_status_applied_label": "Tillämpad",
        "gpc_status_overridden_label": "Åsidosatt",
        "gpc_title": "Global sekretesskontroll identifierad",
    },
    "tr": {
        "gpc_label": "Global Gizlilik Kontrolü",
        "gpc_description": "Global gizlilik kontrolü tercihiniz yerine getirildi. Global gizlilik kontrolüne uygun veri kullanım durumlarından otomatik olarak çıkarıldınız.",
        "gpc_status_applied_label": "Uygulandı",
        "gpc_status_overridden_label": "Geçersiz kılındı",
        "gpc_title": "Genel Gizlilik Kontrolü algılandı",
    },
    "uk": {
        "gpc_label": "Глобальний контроль конфіденційності",
        "gpc_description": "Ваші глобальні налаштування конфіденційності були враховані. Вас було автоматично виключено з випадків використання даних, які дотримуються глобального контролю конфіденційності.",
        "gpc_status_applied_label": "Застосовано",
        "gpc_status_overridden_label": "Перевизначено",
        "gpc_title": "Виявлено глобальний контроль конфіденційності",
    },
    "zh": {
        "gpc_label": "全球隐私控制",
        "gpc_description": "您的全球隐私控制偏好已被尊重。您已自动退出遵守全球隐私控制的数据使用案例。",
        "gpc_status_applied_label": "已应用",
        "gpc_status_overridden_label": "已覆盖",
        "gpc_title": "检测到全球隐私控制",
    },
    "zh-Hant": {
        "gpc_label": "全球隱私控制",
        "gpc_description": "您的全球隱私控制偏好已被尊重。您已自動退出遵守全球隱私控制的資料使用案例。",
        "gpc_status_applied_label": "已套用",
        "gpc_status_overridden_label": "已覆寫",
        "gpc_title": "偵測到全球隱私控制",
    },
}
# fmt: on


def upgrade():
    # Add GPC columns to experiencetranslation table
    op.add_column(
        "experiencetranslation",
        sa.Column("gpc_label", sa.String(), nullable=True),
    )
    op.add_column(
        "experiencetranslation",
        sa.Column("gpc_description", sa.String(), nullable=True),
    )
    op.add_column(
        "experiencetranslation",
        sa.Column("gpc_status_applied_label", sa.String(), nullable=True),
    )
    op.add_column(
        "experiencetranslation",
        sa.Column("gpc_status_overridden_label", sa.String(), nullable=True),
    )
    op.add_column(
        "experiencetranslation",
        sa.Column("gpc_title", sa.String(), nullable=True),
    )

    # Add GPC columns to privacyexperienceconfighistory table
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("gpc_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("gpc_description", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("gpc_status_applied_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("gpc_status_overridden_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("gpc_title", sa.String(), nullable=True),
    )

    # Populate default values for existing translations in all supported languages
    connection = op.get_bind()
    for language, translations in GPC_TRANSLATIONS.items():
        result = connection.execute(
            sa.text(
                """
                UPDATE experiencetranslation
                SET gpc_label = :gpc_label,
                    gpc_description = :gpc_description,
                    gpc_status_applied_label = :gpc_status_applied_label,
                    gpc_status_overridden_label = :gpc_status_overridden_label,
                    gpc_title = :gpc_title
                WHERE language = :language
                """
            ),
            {**translations, "language": language},
        )
        if result.rowcount > 0:
            logger.info(
                f"Updated {result.rowcount} experience translation(s) for language '{language}' with GPC defaults"
            )


def downgrade():
    # Drop columns from privacyexperienceconfighistory
    op.drop_column("privacyexperienceconfighistory", "gpc_title")
    op.drop_column("privacyexperienceconfighistory", "gpc_status_overridden_label")
    op.drop_column("privacyexperienceconfighistory", "gpc_status_applied_label")
    op.drop_column("privacyexperienceconfighistory", "gpc_description")
    op.drop_column("privacyexperienceconfighistory", "gpc_label")

    # Drop columns from experiencetranslation
    op.drop_column("experiencetranslation", "gpc_title")
    op.drop_column("experiencetranslation", "gpc_status_overridden_label")
    op.drop_column("experiencetranslation", "gpc_status_applied_label")
    op.drop_column("experiencetranslation", "gpc_description")
    op.drop_column("experiencetranslation", "gpc_label")
