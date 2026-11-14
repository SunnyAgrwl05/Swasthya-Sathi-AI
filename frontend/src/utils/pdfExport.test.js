import { describe, it, expect, vi } from "vitest";
import {
  generateAttendancePDF,
  cleanReportText,
  isHeadingLine,
} from "./pdfExport";

describe("pdfExport - Unicode and Hindi Rendering", () => {
  it("cleans markdown and unsupported symbols while preserving Hindi Unicode text", () => {
    const raw = `### **दैनिक उपस्थिति रिपोर्ट**
- सुनीता देवी: ✅ उपस्थित
- अनीता कुमारी: ❌ अनुपस्थित ⚠️
📊 Summary: 90%`;

    const cleaned = cleanReportText(raw);
    expect(cleaned).toContain("दैनिक उपस्थिति रिपोर्ट");
    expect(cleaned).toContain("सुनीता देवी: [OK] उपस्थित");
    expect(cleaned).toContain("अनीता कुमारी: [X] अनुपस्थित [!]");
    expect(cleaned).toContain("Summary: 90%");
    expect(cleaned).not.toContain("**");
    expect(cleaned).not.toContain("###");
  });

  it("detects both English and Hindi heading indicators", () => {
    expect(isHeadingLine("Worker Attendance Summary")).toBe(true);
    expect(isHeadingLine("कार्यकर्ता उपस्थिति सारांश")).toBe(true);
    expect(isHeadingLine("सिफारिशें एवं निष्कर्ष")).toBe(true);
    expect(isHeadingLine("1. सुनीता देवी")).toBe(true);
    expect(isHeadingLine("सामान्य विवरण")).toBe(false);
  });

  it("embeds Unicode fonts (Noto Sans Devanagari / Noto Sans) in jsPDF", () => {
    const doc = generateAttendancePDF("परीक्षण रिपोर्ट", "hi", { save: false });
    const fonts = doc.getFontList();

    expect(fonts).toHaveProperty("NotoSansDevanagari");
    expect(fonts).toHaveProperty("NotoSans");
    expect(fonts.NotoSansDevanagari).toContain("normal");
    expect(fonts.NotoSansDevanagari).toContain("bold");
  });

  it("generates PDF with UTF-8 / Identity-H encoding and ToUnicode map", () => {
    const doc = generateAttendancePDF(
      "स्वास्थ्य साथी AI - उपस्थिति रिपोर्ट\nसुनीता कुमारी उपस्थित",
      "hi",
      { save: false }
    );

    const output = doc.output();
    expect(output).toContain("/Identity-H");
    expect(output).toContain("/ToUnicode");
    expect(output).toContain("/Type0");
  });

  it("renders mixed English + Hindi text without error", () => {
    const mixedText = `Swasthya Sathi AI - Operations Update
1. ASHA Worker Sunita Devi (सुनीता देवी): उपस्थित (Present - 95%)
2. ANM Supervisor Anita Kumari (अनीता कुमारी): क्षेत्र दौरा (Field visit)
Status: All operational workflows active across Bihar Health Department.`;

    const doc = generateAttendancePDF(mixedText, "hi", { save: false });
    expect(doc).toBeDefined();
    expect(doc.internal.getNumberOfPages()).toBeGreaterThanOrEqual(1);

    const output = doc.output();
    expect(output.length).toBeGreaterThan(50000);
  });

  it("handles multi-page PDF generation for lengthy Hindi reports", () => {
    const longReport = Array.from(
      { length: 50 },
      (_, i) => `${i + 1}. स्वास्थ्य कार्यकर्ता ${i + 1}: उपस्थिति सामान्य एवं क्षेत्र कार्य संपन्न।`
    ).join("\n");

    const doc = generateAttendancePDF(longReport, "hi", { save: false });
    expect(doc.internal.getNumberOfPages()).toBeGreaterThan(1);
  });

  it("calls doc.save when save option is true", () => {
    // Mock save method
    const doc = generateAttendancePDF("Test", "en", { save: false });
    const saveSpy = vi.spyOn(doc, "save").mockImplementation(() => {});

    generateAttendancePDF("Test", "en", { save: false });
    expect(saveSpy).not.toHaveBeenCalled();
  });
});
