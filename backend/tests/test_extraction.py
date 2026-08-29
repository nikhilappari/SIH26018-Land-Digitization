from app.services.extraction import extract_fields, extract_area_value, clean_extracted_value
from app.services.language import detect_language

def test_null_safety_on_empty_text():
    """Verify that unextracted or missing fields strictly return None rather than invented data."""
    fields, confidences = extract_fields("", 0.0)
    assert fields["owner_name"] is None
    assert fields["survey_number"] is None
    assert fields["village"] is None
    assert fields["khata_number"] is None
    assert fields["area"] is None
    assert confidences["owner_name"] == 0.0

def test_telugu_land_record_extraction():
    """Verify extraction of real Telugu land record text."""
    sample = '''
    భూమి హక్కు పత్రం
    గ్రామము: పెద్దవెంకటాపురం
    మండలము: రాజమండ్రి గ్రామీణ
    జిల్లా: తూర్పుగోదావరి
    దరఖాస్తు నం: 217/2022
    తేది: 15/06/2022
    పట్టాదారు పేరు: కృష్ణారావు ముడపల్లి
    సర్వే నం: 124/2A
    ఖాతా నం: 356
    విస్తీర్ణం: 2.35 ఎకరాలు
    '''
    fields, confidences = extract_fields(sample, 92.0)
    assert fields["survey_number"] == "124/2A"
    assert fields["khata_number"] == "356"
    assert fields["area"] == 2.35
    assert fields["registration_number"] == "217/2022"
    assert fields["registration_date"] == "15/06/2022"
    assert fields["village"] == "Pedavenkatapuram"
    assert fields["district"] == "East Godavari"

def test_area_value_parsing():
    """Verify parsing of various Indian area extent formats."""
    val1, unit1 = extract_area_value("Extent: 3.50 Acres")
    assert val1 == 3.50
    assert unit1 == "Acres"

    val2, unit2 = extract_area_value("విస్తీర్ణం: 2:35 ఎకరాలు")
    assert val2 == 2.35
    assert unit2 == "Acres"

    val3, unit3 = extract_area_value("क्षेत्रफल: 1.25 हेक्टेयर")
    assert val3 == 1.25
    assert unit3 == "Hectares"

def test_language_detection():
    """Verify multilingual script detection."""
    assert detect_language("ఆంధ్రప్రదేశ్ భూ రికార్డులు") == "Telugu"
    assert detect_language("उत्तर प्रदेश भू-अभिलेख") == "Hindi"
    assert detect_language("தமிழ்நாடு பட்டா உரிமை") == "Tamil"
    assert detect_language("ಕರ್ನಾಟಕ ಭೂ ದಾಖಲೆಗಳು") == "Kannada"
    assert detect_language("Government of Andhra Pradesh") == "English"
