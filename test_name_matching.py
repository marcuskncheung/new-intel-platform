#!/usr/bin/env python3
"""
Test POI Name Matching System
Tests the improved calculate_name_similarity() function

Run: python test_name_matching.py
"""

import sys
sys.path.insert(0, '/Users/iapanel/Downloads/new-intel-platform-main')

from alleged_person_automation import calculate_name_similarity, normalize_name_for_matching

def test_name_matching():
    """Test various name matching scenarios"""
    
    print("\n" + "="*80)
    print("POI NAME MATCHING TEST SUITE")
    print("="*80)
    
    tests = [
        # Format: (name1, name2, expected_result, description)
        
        # ===== SINGLE-WORD PROTECTION TESTS =====
        ("LEUNG", "LEUNG TAI LIN", "< 0.85", "Single surname should NOT match full name"),
        ("CHAN", "CHAN KIN WAH", "< 0.85", "Single surname should NOT match full name"),
        ("Wong", "Wong Fei Hung", "< 0.85", "Single surname should NOT match full name"),
        ("LEE", "LEE KA MAN", "< 0.85", "Single surname should NOT match full name"),
        
        # ===== SAME PERSON VARIATIONS =====
        ("John Smith", "John Smith", "= 1.0", "Exact match"),
        ("Cao Yue", "Cao Yue Spero", ">= 0.85", "Same person with nickname suffix"),
        ("Peter Chan", "Chan Peter", ">= 0.85", "Same name different order"),
        ("CHAN WEI MING", "WEI MING CHAN", ">= 0.85", "Same name parts reordered"),
        
        # ===== COMPANY VS PERSON =====
        ("Wong Property Limited", "Wong Ka Ming", "= 0.0", "Company vs person"),
        ("Chan Holdings Group", "Chan Wai Kei", "= 0.0", "Company vs person"),
        ("ABC Financial Services", "ABC Lee", "= 0.0", "Company vs person"),
        ("星輝地產有限公司", "星輝明", "= 0.0", "Chinese company vs person"),
        
        # ===== CHINESE NAME TESTS =====
        ("陳偉明", "陳偉明", "= 1.0", "Exact Chinese match"),
        ("曹越", "曹越spero", ">= 0.90", "Chinese + English suffix"),
        ("陳偉明", "陳偉銘", "< 0.85", "Different last character (銘 vs 明)"),
        ("王", "王大明", "< 0.85", "Single Chinese char vs full name"),
        
        # ===== SIMILAR BUT DIFFERENT =====
        ("John Smith", "John Smyth", "varies", "Similar spelling (could be typo)"),
        ("Lee Ka Ming", "Lee Ka Man", "varies", "Similar names different person"),
        ("Wong Tai Sin", "Wong Tai Sing", "varies", "Similar names (could be same)"),
        
        # ===== EDGE CASES =====
        ("", "John Smith", "= 0.0", "Empty name"),
        ("John Smith", "", "= 0.0", "Empty name"),
        ("", "", "= 0.0", "Both empty"),
        ("A", "B", "< 0.85", "Single letters"),
        ("ABC", "ABC DEF", "< 0.85", "Short word vs longer"),
    ]
    
    passed = 0
    failed = 0
    
    for name1, name2, expected, description in tests:
        similarity = calculate_name_similarity(name1, name2)
        
        # Parse expected
        if expected == "= 1.0":
            success = similarity == 1.0
        elif expected == "= 0.0":
            success = similarity == 0.0
        elif expected.startswith(">= "):
            threshold = float(expected.split()[1])
            success = similarity >= threshold
        elif expected.startswith("< "):
            threshold = float(expected.split()[1])
            success = similarity < threshold
        elif expected == "varies":
            success = True  # Just for information
        else:
            success = True
        
        status = "✅ PASS" if success else "❌ FAIL"
        if not success:
            failed += 1
        else:
            passed += 1
        
        print(f"\n{status}: {description}")
        print(f"  '{name1}' vs '{name2}'")
        print(f"  Expected: {expected}, Got: {similarity:.3f}")
    
    print("\n" + "="*80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0

def test_normalize_name():
    """Test name normalization"""
    
    print("\n" + "="*80)
    print("NAME NORMALIZATION TESTS")
    print("="*80)
    
    tests = [
        ("  John  Smith  ", "john smith", "Whitespace trimming"),
        ("MR. John Smith", "john smith", "Mr. prefix removal"),
        ("Dr. Lee Ka Ming", "lee ka ming", "Dr. prefix removal"),
        ("CHAN WEI MING", "chan wei ming", "Uppercase to lowercase"),
        ("Ms. Wong Mei Ling", "wong mei ling", "Ms. prefix removal"),
    ]
    
    for name, expected, description in tests:
        result = normalize_name_for_matching(name)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"\n{status}: {description}")
        print(f"  Input: '{name}'")
        print(f"  Expected: '{expected}', Got: '{result}'")
    
    print("\n")

if __name__ == "__main__":
    print("\n🧪 Running POI Name Matching Tests...\n")
    
    test_normalize_name()
    success = test_name_matching()
    
    if success:
        print("\n✅ All critical tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed - review the output above")
        sys.exit(1)
