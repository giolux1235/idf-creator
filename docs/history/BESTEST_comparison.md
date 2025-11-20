# BESTEST-GSR vs IDF Creator - Comparison

## Both Generate IDFs, But Differently

### BESTEST-GSR (Validation Tool)

**What it generates:**
- ✅ Standardized test case IDFs (97 cases)
- ✅ Controlled reference models for validation
- ✅ ASHRAE Standard 140 compliant test buildings
- ❌ NOT for real-world buildings
- ❌ NOT from user addresses/input

**How it works:**
1. Uses `bestest_case_var_lib.rb` to define test parameters
2. Loads standardized resources (`bestest_resources.osm`)
3. Applies specific test case configurations
4. Generates test IDF for validation purposes

**Use case:** Testing simulation engines, not creating custom models

---

### Your IDF Creator (Real-World Tool)

**What it generates:**
- ✅ Custom IDFs from ANY address
- ✅ Real-world building models
- ✅ User-specified building types
- ✅ Models extracted from documents (PDFs, images)
- ✅ Practical simulation-ready files

**How it works:**
1. Geocodes address to get location
2. Parses documents for building info
3. Estimates missing parameters
4. Generates custom IDF tailored to user input

**Use case:** Creating models for actual buildings

---

## Key Difference

| Feature | BESTEST-GSR | IDF Creator |
|---------|-------------|-------------|
| **Input** | Test case number | Real address, documents |
| **Purpose** | Validation/testing | Actual modeling |
| **Output** | Standardized test IDF | Custom building IDF |
| **Use case** | Quality assurance | Real projects |
| **Target** | Simulation engines | Building designers |

---

## Could You Combine Them?

**Yes! Here's how:**

1. **Use IDF Creator** to generate a real building IDF
2. **Use BESTEST-GSR** to validate that IDF quality
3. **Get both:** Custom model + quality assurance

```python
# Future workflow
idf_file = creator.create_idf("123 Main St, NYC")
bestest_validation = validator.test_idf(idf_file)
print(f"Your IDF scores {bestest_validation.score} on Standard 140 tests")
```

---

## Bottom Line

- **BESTEST-GSR:** Generates test IDEs (validation tool)
- **IDF Creator:** Generates real-world IDFs (your tool)
- **Together:** They complement each other!











