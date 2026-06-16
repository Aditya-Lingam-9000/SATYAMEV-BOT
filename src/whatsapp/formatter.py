"""
WhatsApp Response Formatter

Formats verdicts and information into WhatsApp-friendly messages.
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class WhatsAppFormatter:
    """Formats verification results for WhatsApp display."""
    
    # Verdict emojis and text
    VERDICT_EMOJI = {
        "TRUE": "✅",
        "FALSE": "❌",
        "MISLEADING": "⚠️",
        "UNVERIFIABLE": "❓",
    }
    
    VERDICT_TEXT = {
        "TRUE": "TRUE",
        "FALSE": "FALSE",
        "MISLEADING": "MISLEADING",
        "UNVERIFIABLE": "UNVERIFIABLE",
    }
    
    VERDICT_COLOR = {
        "TRUE": "🟢",
        "FALSE": "🔴",
        "MISLEADING": "🟠",
        "UNVERIFIABLE": "🔵",
    }
    
    # Multilingual translation mapping for labels
    LANG_TEMPLATES = {
        "english": {
            "verdict_title": "VERDICT",
            "confidence": "Confidence Level",
            "analysis": "Analysis",
            "supporting_evidence": "Supporting Evidence",
            "verified_sources": "Verified Sources",
            "footer_title": "Fact-Check by Satyamev-Bot",
            "footer_sub": "Powered by AI & Trusted Sources",
            "ingest_failed": "FACT-CHECK FAILED",
            "ingest_failed_desc": "We couldn't process your request:",
            "ingest_failed_bullets": "Please try again with:\n• A text claim\n• A screenshot or image\n• A voice message"
        },
        "hindi": {
            "verdict_title": "निर्णय",
            "confidence": "विश्वास का स्तर",
            "analysis": "विश्लेषण",
            "supporting_evidence": "सहायक साक्ष्य",
            "verified_sources": "सत्यापित स्रोत",
            "footer_title": "सत्यमेव-बॉट द्वारा तथ्य-जांच",
            "footer_sub": "AI और विश्वसनीय स्रोतों द्वारा संचालित",
            "ingest_failed": "तथ्य-जांच विफल",
            "ingest_failed_desc": "हम आपके अनुरोध को संसाधित नहीं कर सके:",
            "ingest_failed_bullets": "कृपया पुनः प्रयास करें:\n• एक टेक्स्ट दावा\n• एक स्क्रीनशॉट या छवि\n• एक वॉयस संदेश"
        },
        "telugu": {
            "verdict_title": "తీర్పు",
            "confidence": "విశ్వసనీయత స్థాయి",
            "analysis": "విశ్లేషణ",
            "supporting_evidence": "సహాయక ఆధారాలు",
            "verified_sources": "ధృవీకరించబడిన మూలాలు",
            "footer_title": "సత్యమేవ్-బాట్ ద్వారా ఫ్యాక్ట్-చెక్",
            "footer_sub": "AI & విశ్వసनीय మూలాల ద్వారా నడపబడుతుంది",
            "ingest_failed": "ఫ్యాక్ట్-చెక్ విఫలమైంది",
            "ingest_failed_desc": "మేము మీ అభ్యర్థనను ప్రాసెస్ చేయలేకపోయాము:",
            "ingest_failed_bullets": "దయచేసి వీటితో మళ్ళీ ప్రయత్నించండి:\n• ఒక టెక్స్ట్ క్లెయిమ్\n• ఒక స్క్రీన్ షాట్ లేదా చిత్రం\n• ఒక వాయిస్ మెసేజ్"
        },
        "tamil": {
            "verdict_title": "தீர்ப்பு",
            "confidence": "நம்பிக்கை நிலை",
            "analysis": "பகுப்பாய்வு",
            "supporting_evidence": "ஆதார சான்றுகள்",
            "verified_sources": "சரிபார்க்கப்பட்ட ஆதாரங்கள்",
            "footer_title": "சத்யமேவ்-பாட் மூலம் உண்மை சரிபார்ப்பு",
            "footer_sub": "AI & நம்பகமான ஆதாரங்கள் மூலம் இயக்கப்படுகிறது",
            "ingest_failed": "உண்மை சரிபார்ப்பு தோல்வி",
            "ingest_failed_desc": "உங்கள் கோரிக்கையை எங்களால் செயல்படுத்த முடியவில்லை:",
            "ingest_failed_bullets": "தயவுசெய்து மீண்டும் முயற்சிக்கவும்:\n• ஒரு உரை கூற்று\n• ஒரு ஸ்கிரீன்ஷாட் அல்லது படம்\n• ஒரு குரல் செய்தி"
        },
        "marathi": {
            "verdict_title": "निष्कर्ष",
            "confidence": "विश्वास पातळी",
            "analysis": "विश्लेषण",
            "supporting_evidence": "सहाय्यक पुरावे",
            "verified_sources": "सत्यापित स्रोत",
            "footer_title": "सत्यमेव-बॉट द्वारे तथ्य-तपासणी",
            "footer_sub": "AI आणि विश्वसनीय स्रोतांद्वारे संचलित",
            "ingest_failed": "तथ्य-तपासणी यशस्वी झाली नाही",
            "ingest_failed_desc": "आम्ही आपल्या विनंतीवर प्रक्रिया करू शकलो नाही:",
            "ingest_failed_bullets": "कृपया पुन्हा प्रयत्न करा:\n• एक मजकूर दावा\n• एक स्क्रीनशॉट किंवा प्रतिमा\n• एक व्हॉइस संदेश"
        },
        "gujarati": {
            "verdict_title": "ચુકાદો",
            "confidence": "વિશ્વાસનું સ્તર",
            "analysis": "વિશ્લેષણ",
            "supporting_evidence": "સહાયક પુરાવા",
            "verified_sources": "સત્યાપિત સ્ત્રોતો",
            "footer_title": "સત્યમેવ-બોટ દ્વારા ફેક્ટ-ચેક",
            "footer_sub": "AI અને વિશ્વસનીય સ્ત્રોતો દ્વારા સંચાલિત",
            "ingest_failed": "ફેક્ટ-ચેક નિષ્ફળ",
            "ingest_failed_desc": "અમે તમારી વિનંતી પર પ્રક્રિયા કરી શક્યા નથી:",
            "ingest_failed_bullets": "કૃપા કરીને ફરીથી પ્રયાસ કરો:\n• ટેક્સ્ટ દાવો\n• સ્ક્રીનશોટ અથવા છબી\n• વૉઇસ સંદેશ"
        },
        "urdu": {
            "verdict_title": "فیصلہ",
            "confidence": "اعتماد کی سطح",
            "analysis": "تجزیہ",
            "supporting_evidence": "معاون ثبوت",
            "verified_sources": "تصدیق شدہ ذرائع",
            "footer_title": "ستیہ میو بوٹ کے ذریعے فیکٹ چیک",
            "footer_sub": "مصنوعی ذہانت اور قابل اعتماد ذرائع سے لیس",
            "ingest_failed": "فیکٹ چیک ناکام ہو گیا",
            "ingest_failed_desc": "ہم آپ کی درخواست پر کارروائی نہیں کر سکے:",
            "ingest_failed_bullets": "براہ کرم دوبارہ کوشش کریں:\n• ایک ٹیکسٹ دعویٰ\n• ایک اسکرین شاٹ یا تصویر\n• ایک صوتی پیغام"
        },
        "kannada": {
            "verdict_title": "ತೀರ್ಪು",
            "confidence": "ವಿಶ್ವಾಸಾರ್ಹತೆಯ ಮಟ್ಟ",
            "analysis": "ವಿಶ್ಲೇಷಣೆ",
            "supporting_evidence": "ಪೂರಕ ಪುರಾವೆಗಳು",
            "verified_sources": "ಪರಿಶೀಲಿಸಿದ ಮೂಲಗಳು",
            "footer_title": "ಸತ್ಯಮೇವ್-ಬಾಟ್ ಮೂಲಕ ಫ್ಯಾಕ್ಟ್-ಚೆಕ್",
            "footer_sub": "AI ಮತ್ತು ವಿಶ್ವಾಸಾರ್ಹ ಮೂಲಗಳಿಂದ ನಡೆಸಲ್ಪಡುತ್ತದೆ",
            "ingest_failed": "ಕಡತ ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲು ಸಾಧ್ಯವಾಗಿಲ್ಲ",
            "ingest_failed_desc": "ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲು ನಮಗೆ ಸಾಧ್ಯವಾಗಲಿಲ್ಲ:",
            "ingest_failed_bullets": "ದಯವಿಟ್ಟು ಇವುಗಳೊಂದಿಗೆ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ:\n• ಪಠ್ಯ ಹಕ್ಕು\n• ಸ್ಕ್ರೀನ್‌ಶಾಟ್ ಅಥವಾ ಚಿತ್ರ\n• ಧ್ವನಿ ಸಂದೇಶ"
        },
        "odia": {
            "verdict_title": "ନିଷ୍ପତ୍ତି",
            "confidence": "ବିଶ୍ୱାସର ସ୍ତର",
            "analysis": "ବିଶ୍ଳେଷଣ",
            "supporting_evidence": "ସହାୟକ ପ୍ରମାଣ",
            "verified_sources": "ଯାଞ୍ચ ହୋଇଥିବା ଉତ୍ସ",
            "footer_title": "ସତ୍ୟମେବ-ବଟ୍ ଦ୍ୱାରା ତଥ୍ୟ ଯାଞ୍ಚ",
            "footer_sub": "AI ଏବଂ ବିଶ୍ୱାସଯୋગ୍ୟ ଉତ୍ସ ଦ୍ୱାରା ଚାଳିତ",
            "ingest_failed": "ତଥ୍ୟ ଯାଞ୍ಚ ବିଫଳ ହେଲା",
            "ingest_failed_desc": "ଆମେ ଆପڻଙ୍କ ଅନຸରୋଧ ପ୍ରକ୍ରିୟାକରଣ କରିପାରିଲୁ ନାହିଁ:",
            "ingest_failed_bullets": "ଦୟାକରି ପୁଣિ ଚେଷ୍ଟା କରନ୍ତു:\n• ଏକ ଲେଖା ଦାବି\n• ଏକ ସ୍କ୍ରିନସଟ୍ କିମ୍ବା ଛବି\n• ଏକ ସ୍ୱର ବାର୍ତ୍ତା"
        },
        "malayalam": {
            "verdict_title": "തീർപ്പ്",
            "confidence": "വിശ്വാസ്യതയുടെ നിലവാരം",
            "analysis": "വിശകലനം",
            "supporting_evidence": "സഹായകരമായ തെളിവുകൾ",
            "verified_sources": "സ്ഥിരീകരിച്ച ഉറവിടങ്ങൾ",
            "footer_title": "സത്യമേവ്-ബോട്ട് വഴിയുള്ള വസ്തുതാ പരിശോധന",
            "footer_sub": "AI-യും വിശ്വസനീയമായ ഉറവിടങ്ങളും അടിസ്ഥാനമാക്കിയത്",
            "ingest_failed": "വസ്തുതാ പരിശോധന പരാജയപ്പെട്ടു",
            "ingest_failed_desc": "നിങ്ങളുടെ അഭ്യർത്ഥന പ്രോസസ്സ് ചെയ്യാൻ ഞങ്ങൾക്ക് കഴിഞ്ഞില്ല:",
            "ingest_failed_bullets": "ദയവായി താഴെ പറയുന്നവ ഉപയോഗിച്ച് വീണ്ടും ശ്രമിക്കുക:\n• ഒരു വാചക ക്ലെയിം\n• ഒരു സ്ക്രീൻഷോട്ട് അല്ലെങ്കിൽ ചിത്രം\n• ഒരു ശബ്ദ സന്ദേശം"
        },
        "bengali": {
            "verdict_title": "রায়",
            "confidence": "বিশ্বাসের স্তর",
            "analysis": "বিশ্লেষণ",
            "supporting_evidence": "সহায়ক প্রমাণ",
            "verified_sources": "যাচাইকৃত উৎস",
            "footer_title": "সত্যমেব-বট দ্বারা ফ্যাক্ট-চেক",
            "footer_sub": "AI এবং বিশ্বস্ত উৎস দ্বারা চালিত",
            "ingest_failed": "ফ্যাক্ট-চেক ব্যর্থ হয়েছে",
            "ingest_failed_desc": "আমরা আপনার অনুরোধটি প্রক্রিয়াকরণ করতে পারিনি:",
            "ingest_failed_bullets": "অনুগ্রহ করে আবার চেষ্টা করুন:\n• একটি টেক্সট দাবি\n• একটি স্ক্রিনশট বা ছবি\n• একটি ভয়েস বার্তা"
        }
    }
    
    VERDICT_TRANSLATIONS = {
        "english": {
            "TRUE": "TRUE",
            "FALSE": "FALSE",
            "MISLEADING": "MISLEADING",
            "UNVERIFIABLE": "UNVERIFIABLE",
        },
        "hindi": {
            "TRUE": "सत्य (TRUE)",
            "FALSE": "असत्य (FALSE)",
            "MISLEADING": "भ्रामक (MISLEADING)",
            "UNVERIFIABLE": "अपुष्ट (UNVERIFIABLE)",
        },
        "telugu": {
            "TRUE": "నిజం (TRUE)",
            "FALSE": "అబద్ధం (FALSE)",
            "MISLEADING": "తప్పుదోవ పట్టించేది (MISLEADING)",
            "UNVERIFIABLE": "ధృవీకరించబడలేదు (UNVERIFIABLE)",
        },
        "tamil": {
            "TRUE": "உண்மை (TRUE)",
            "FALSE": "பொய் (FALSE)",
            "MISLEADING": "தவறான தகவல் (MISLEADING)",
            "UNVERIFIABLE": "சரிபார்க்க முடியவில்லை (UNVERIFIABLE)",
        },
        "marathi": {
            "TRUE": "सत्य (TRUE)",
            "FALSE": "असत्य (FALSE)",
            "MISLEADING": "दिशाभूल करणारे (MISLEADING)",
            "UNVERIFIABLE": "पडताळणी न झालेले (UNVERIFIABLE)",
        },
        "gujarati": {
            "TRUE": "સાચું (TRUE)",
            "FALSE": "ખોટું (FALSE)",
            "MISLEADING": "ભ્રામક (MISLEADING)",
            "UNVERIFIABLE": "ચકાસી ન શકાય તેવું (UNVERIFIABLE)",
        },
        "urdu": {
            "TRUE": "سچ (TRUE)",
            "FALSE": "جھوٹ (FALSE)",
            "MISLEADING": "گمراہ کن (MISLEADING)",
            "UNVERIFIABLE": "تصدیق ناممکن (UNVERIFIABLE)",
        },
        "kannada": {
            "TRUE": "ನಿಜ (TRUE)",
            "FALSE": "ಸುಳ್ಳು (FALSE)",
            "MISLEADING": "ದಾರಿ ತಪ್ಪಿಸುವ (MISLEADING)",
            "UNVERIFIABLE": "ಪರಿಶೀಲಿಸಲಾಗದ (UNVERIFIABLE)",
        },
        "odia": {
            "TRUE": "ସତ୍ୟ (TRUE)",
            "FALSE": "ମିଥ୍ୟା (FALSE)",
            "MISLEADING": "ଭ୍ରମାତ୍ମକ (MISLEADING)",
            "UNVERIFIABLE": "ଯାଞ୍চ ଅସମ୍ଭବ (UNVERIFIABLE)",
        },
        "malayalam": {
            "TRUE": "ശരി (TRUE)",
            "FALSE": "തെറ്റ് (FALSE)",
            "MISLEADING": "തെറ്റിദ്ധരിപ്പിക്കുന്നത് (MISLEADING)",
            "UNVERIFIABLE": "സ്ഥിരീകരിക്കാൻ കഴിയാത്തത് (UNVERIFIABLE)",
        },
        "bengali": {
            "TRUE": "সত্য (TRUE)",
            "FALSE": "মিথ্যা (FALSE)",
            "MISLEADING": "বিভ্রান্তিকর (MISLEADING)",
            "UNVERIFIABLE": "যাচাই করা অসম্ভব (UNVERIFIABLE)",
        }
    }

    @staticmethod
    def _get_lang_key(lang: str) -> str:
        if not lang:
            return "english"
        lang_lower = lang.lower()
        if "hindi" in lang_lower or lang_lower == "hi":
            return "hindi"
        elif "telugu" in lang_lower or lang_lower == "te":
            return "telugu"
        elif "tamil" in lang_lower or lang_lower == "ta":
            return "tamil"
        elif "marathi" in lang_lower or lang_lower == "mr":
            return "marathi"
        elif "bengali" in lang_lower or lang_lower == "bn":
            return "bengali"
        elif "gujarati" in lang_lower or lang_lower == "gu":
            return "gujarati"
        elif "urdu" in lang_lower or lang_lower == "ur":
            return "urdu"
        elif "kannada" in lang_lower or lang_lower == "kn":
            return "kannada"
        elif "odia" in lang_lower or lang_lower == "or":
            return "odia"
        elif "malayalam" in lang_lower or lang_lower == "ml":
            return "malayalam"
        return "english"

    @staticmethod
    def format_verdict_message(result: Dict) -> str:
        """
        Format verification result as WhatsApp message.
        Professional, comprehensive formatting with medium-length analysis.
        
        Args:
            result: Result dictionary from WhatsAppHandler.process_message()
        
        Returns:
            Formatted WhatsApp message text
        """
        language = result.get("language", "English")
        lang_key = WhatsAppFormatter._get_lang_key(language)
        templates = WhatsAppFormatter.LANG_TEMPLATES.get(lang_key, WhatsAppFormatter.LANG_TEMPLATES["english"])
        
        if not result.get("success"):
            error = result.get("error", "Unknown error occurred")
            return (
                f"*{templates['ingest_failed']}*\n\n"
                f"{templates['ingest_failed_desc']}\n\n"
                f"_{error}_\n\n"
                f"{templates['ingest_failed_bullets']}"
            )
        
        verdict = result.get("verdict", "UNVERIFIABLE")
        confidence = result.get("confidence", 0)
        reasoning = result.get("reasoning", "No explanation available")
        sources = result.get("sources", [])
        key_evidence = result.get("key_evidence", [])
        
        # Build message
        emoji = WhatsAppFormatter.VERDICT_EMOJI.get(verdict, "❓")
        
        # Translate the verdict category text
        verdict_trans_dict = WhatsAppFormatter.VERDICT_TRANSLATIONS.get(lang_key, WhatsAppFormatter.VERDICT_TRANSLATIONS["english"])
        translated_verdict = verdict_trans_dict.get(verdict, verdict)
        
        message_lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"{emoji} *{templates['verdict_title']}: {translated_verdict}*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ]
        
        # Confidence indicator
        confidence_bars = WhatsAppFormatter._get_confidence_bar(confidence)
        message_lines.append(f"*{templates['confidence']}:* {confidence_bars} {confidence:.0%}")
        message_lines.append("")
        
        # Detailed Reasoning (medium length ~400-500 chars)
        reasoning_text = reasoning[:450] + "..." if len(reasoning) > 450 else reasoning
        message_lines.append(f"*{templates['analysis']}:*")
        message_lines.append(reasoning_text)
        message_lines.append("")
        
        # Key evidence (4-5 points)
        if key_evidence:
            message_lines.append(f"*{templates['supporting_evidence']}:*")
            # Display 4-5 evidence points
            for i, evidence in enumerate(key_evidence[:5], 1):
                # Keep more text per evidence point (100 chars instead of 80)
                evidence_text = evidence[:120] + "..." if len(evidence) > 120 else evidence
                message_lines.append(f"{i}. {evidence_text}")
            message_lines.append("")
        
        # Sources (3-4 URLs)
        if sources:
            message_lines.append(f"*{templates['verified_sources']}:*")
            source_count = min(4, len(sources))  # Show 3-4 sources
            for i, source in enumerate(sources[:source_count], 1):
                # Cleaner URL display
                source_display = source[:60] + "..." if len(source) > 60 else source
                message_lines.append(f"{i}. {source_display}")
            message_lines.append("")
        
        # Professional footer
        message_lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        message_lines.append(templates['footer_title'])
        message_lines.append(templates['footer_sub'])
        
        return "\n".join(message_lines)
    
    @staticmethod
    def format_acknowledgment_message() -> str:
        """Format initial acknowledgment message - professional, minimal emojis, bilingual."""
        return (
            "*Processing Your Claim / आपका दावा संसाधित किया जा रहा है...*\n\n"
            "Our AI verification system is analyzing your claim against trusted databases, "
            "academic sources, and real-time web information.\n"
            "हमारा AI सत्यापन सिस्टम आपके दावे का विश्लेषण कर रहा है।\n\n"
            "⏱ Expected time: 20-60 seconds / अपेक्षित समय: 20-60 सेकंड\n\n"
            "Please wait for the detailed fact-check report / कृपया रिपोर्ट की प्रतीक्षा करें।"
        )
    
    @staticmethod
    def format_error_message(error_type: str = "unknown", language: str = "English") -> str:
        """Format error message for WhatsApp - professional tone."""
        lang_key = WhatsAppFormatter._get_lang_key(language)
        if lang_key == "hindi":
            messages = {
                "timeout": (
                    "*अनुरोध समय समाप्त (Timeout)*\n\n"
                    "सत्यापन प्रक्रिया समय सीमा से अधिक हो गई। यह जटिल दावों के साथ हो सकता है जिनके लिए व्यापक शोध की आवश्यकता होती है।\n\n"
                    "कृपया अधिक विशिष्ट या संक्षिप्त दावे के साथ पुनः प्रयास करें।"
                ),
                "invalid_input": (
                    "*अमान्य इनपुट प्रारूप (Invalid Input)*\n\n"
                    "कृपया निम्नलिखित में से एक भेजें:\n\n"
                    "1. पाठ दावा (10-5000 वर्ण)\n"
                    "2. स्क्रीनशॉट या छवि\n"
                    "3. वॉयस संदेश\n\n"
                    "उदाहरण:\n"
                    "✓ क्या पृथ्वी गोल है?\n"
                    "✓ क्या पानी 100°C पर उबलता है?"
                ),
                "service_error": (
                    "*सेवा अस्थायी रूप से अनुपलब्ध (Service Offline)*\n\n"
                    "हमारी सत्यापन सेवाओं में से एक रखरखाव के लिए वर्तमान में ऑफ़लाइन है।\n\n"
                    "कृपया कुछ क्षणों में पुनः प्रयास करें।"
                ),
                "unknown": (
                    "*सत्यापन त्रुटि (Error)*\n\n"
                    "आपके अनुरोध को संसाधित करते समय एक अप्रत्याशित त्रुटि हुई।\n\n"
                    "कृपया पुनः प्रयास करें। यदि समस्या बनी रहती है, तो सहायता से संपर्क करें।"
                ),
            }
        else:
            messages = {
                "timeout": (
                    "*Request Timeout*\n\n"
                    "The verification process exceeded the time limit. This may occur with complex claims "
                    "requiring extensive research.\n\n"
                    "Please try again with a more specific or concise claim."
                ),
                "invalid_input": (
                    "*Invalid Input Format*\n\n"
                    "Please send one of the following:\n\n"
                    "1. Text claim (10-5000 characters)\n"
                    "2. Screenshot or image\n"
                    "3. Voice message\n\n"
                    "Examples:\n"
                    "✓ Is the Earth flat?\n"
                    "✓ Does water boil at 100°C?"
                ),
                "service_error": (
                    "*Service Temporarily Unavailable*\n\n"
                    "One of our verification services is currently offline for maintenance.\n\n"
                    "Please try again in a few moments."
                ),
                "unknown": (
                    "*Verification Error*\n\n"
                    "An unexpected error occurred while processing your request.\n\n"
                    "Please try again. If the issue persists, contact support."
                ),
            }
        return messages.get(error_type, messages["unknown"])
    
    @staticmethod
    def _get_confidence_bar(confidence: float, length: int = 5) -> str:
        """
        Generate visual confidence bar.
        
        Args:
            confidence: Confidence score (0-1)
            length: Length of bar
        
        Returns:
            Visual bar representation
        """
        filled = int(confidence * length)
        empty = length - filled
        
        bar = "█" * filled + "░" * empty
        return f"[{bar}]"
    
    @staticmethod
    def format_sources_summary(sources: List[str], max_count: int = 4) -> str:
        """Format sources as numbered list with clean URLs."""
        if not sources:
            return "No sources available"
        
        lines = []
        for i, source in enumerate(sources[:max_count], 1):
            # Clean URL display
            display_url = source.replace("https://", "").replace("http://", "")
            display_url = display_url[:50] + "..." if len(display_url) > 50 else display_url
            lines.append(f"{i}. {display_url}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_batch_results(results: List[Dict]) -> str:
        """Format batch verification results - professional format."""
        lines = [
            "*Batch Verification Report*",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ]
        
        verdict_counts = {}
        for result in results:
            verdict = result.get("verdict", "UNVERIFIABLE")
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        
        # Summary Statistics
        lines.append("*Summary:*")
        for verdict, count in verdict_counts.items():
            emoji = WhatsAppFormatter.VERDICT_EMOJI.get(verdict, "❓")
            lines.append(f"{emoji} {verdict}: {count}")
        
        lines.append("")
        lines.append("*Individual Results:*")
        
        # Individual results (limit to 5)
        for i, result in enumerate(results[:5], 1):
            if result.get("success"):
                verdict = result.get("verdict", "UNVERIFIABLE")
                confidence = result.get("confidence", 0)
                emoji = WhatsAppFormatter.VERDICT_EMOJI.get(verdict, "❓")
                lines.append(f"{i}. {emoji} {verdict} ({confidence:.0%})")
            else:
                lines.append(f"{i}. Error: {result.get('error', 'Unknown')[:40]}")
        
        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        return "\n".join(lines)
