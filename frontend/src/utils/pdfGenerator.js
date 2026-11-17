// frontend/src/utils/pdfGenerator.js
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import { NOTO_SANS_DEVANAGARI_REGULAR_BASE64 } from "../fonts/notoSansDevanagari";

const FONT_FILE_NAME = "NotoSansDevanagari-Regular.ttf";
const FONT_FAMILY_NAME = "NotoSansDevanagari";

/**
 * Registers Unicode Devanagari font into jsPDF VFS
 */
function registerUnicodeFonts(doc) {
    doc.addFileToVFS(FONT_FILE_NAME, NOTO_SANS_DEVANAGARI_REGULAR_BASE64);
    doc.addFont(FONT_FILE_NAME, FONT_FAMILY_NAME, "normal");
    // Map bold to the same font (or load NotoSansDevanagari-Bold.ttf if available)
    // so jsPDF never falls back to Helvetica on bold Hindi text
    doc.addFont(FONT_FILE_NAME, FONT_FAMILY_NAME, "bold");
    doc.setFont(FONT_FAMILY_NAME, "normal");
}

/**
 * Normalizes text to NFC Unicode form so conjuncts/matras render consistently
 */
function normalizeUnicode(text) {
    if (!text) return "";
    return String(text).normalize("NFC");
}

/**
 * Exports AI Operations Attendance Analysis Report as a Unicode-safe PDF
 * @param {Object} reportData
 * @param {string} reportData.title - Report Title (English/Hindi)
 * @param {string} reportData.generatedAt - Timestamp string
 * @param {string} reportData.analysisText - AI Markdown/Plain text summary (mixed English + Hindi)
 * @param {Array<Object>} [reportData.attendanceRows] - Optional tabular records
 */
export function exportAttendanceAnalysisPDF(reportData) {
    const {
        title = "Swasthya Sathi AI - Attendance Analysis Report",
        generatedAt = new Date().toLocaleString("en-IN"),
        analysisText = "",
        attendanceRows = [],
    } = reportData;

    const doc = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
        putOnlyUsedFonts: true,
        compress: true,
    });

    // 1. Register and activate Unicode font BEFORE adding any text
    registerUnicodeFonts(doc);

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 15;
    const maxLineWidth = pageWidth - margin * 2;
    let cursorY = 18;

    // 2. Header Banner
    doc.setFillColor(15, 118, 110); // Teal healthcare theme
    doc.rect(0, 0, pageWidth, 28, "F");

    doc.setTextColor(255, 255, 255);
    doc.setFont(FONT_FAMILY_NAME, "bold");
    doc.setFontSize(15);
    doc.text(normalizeUnicode(title), margin, 13);

    doc.setFont(FONT_FAMILY_NAME, "normal");
    doc.setFontSize(9);
    doc.text(normalizeUnicode(`Generated on: ${generatedAt}`), margin, 21);

    cursorY = 38;

    // 3. Optional Attendance Summary Table (if structured data is passed)
    if (Array.isArray(attendanceRows) && attendanceRows.length > 0) {
        autoTable(doc, {
            startY: cursorY,
            head: [["Worker Name / नाम", "Role / पद", "Block / क्षेत्र", "Status / स्थिति"]],
            body: attendanceRows.map((row) => [
                normalizeUnicode(row.name || "-"),
                normalizeUnicode(row.role || "-"),
                normalizeUnicode(row.location || "-"),
                normalizeUnicode(row.status || "-"),
            ]),
            styles: {
                font: FONT_FAMILY_NAME,
                fontStyle: "normal",
                fontSize: 9.5,
                cellPadding: 3,
                textColor: [30, 41, 59],
            },
            headStyles: {
                font: FONT_FAMILY_NAME,
                fontStyle: "bold",
                fillColor: [15, 118, 110],
                textColor: [255, 255, 255],
            },
            alternateRowStyles: {
                fillColor: [240, 253, 250],
            },
            margin: { left: margin, right: margin },
        });

        cursorY = doc.lastAutoTable.finalY + 10;
    }

    // 4. AI Operations Analysis Body (Mixed English + Hindi)
    doc.setTextColor(15, 23, 42);
    doc.setFont(FONT_FAMILY_NAME, "bold");
    doc.setFontSize(12);
    doc.text(normalizeUnicode("AI Operations Analysis / विश्लेषण रिपोर्ट"), margin, cursorY);
    cursorY += 7;

    doc.setDrawColor(203, 213, 225);
    doc.line(margin, cursorY - 2, pageWidth - margin, cursorY - 2);
    cursorY += 4;

    // Strip basic markdown symbols while preserving Hindi matras & punctuation
    const cleanText = normalizeUnicode(
        analysisText
            .replace(/\*\*(.*?)\*\*/g, "$1")
            .replace(/__(.*?)__/g, "$1")
            .replace(/#{1,6}\s?/g, "")
    );

    doc.setFont(FONT_FAMILY_NAME, "normal");
    doc.setFontSize(10.5);
    doc.setTextColor(51, 65, 85);

    const paragraphs = cleanText.split("\n");
    const lineHeight = 6;

    paragraphs.forEach((paragraph) => {
        if (!paragraph.trim()) {
            cursorY += 3;
            return;
        }

        const wrappedLines = doc.splitTextToSize(paragraph, maxLineWidth);
        wrappedLines.forEach((line) => {
            if (cursorY + lineHeight > pageHeight - margin) {
                doc.addPage();
                // Re-apply font on every new page so jsPDF does not reset to Helvetica
                doc.setFont(FONT_FAMILY_NAME, "normal");
                doc.setFontSize(10.5);
                cursorY = margin;
            }
            doc.text(line, margin, cursorY);
            cursorY += lineHeight;
        });
    });

    // 5. Footer with Page Numbers
    const totalPages = doc.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFont(FONT_FAMILY_NAME, "normal");
        doc.setFontSize(8.5);
        doc.setTextColor(100, 116, 139);
        doc.text(
            `Swasthya Sathi AI • Page ${i} of ${totalPages}`,
            pageWidth / 2,
            pageHeight - 8,
            { align: "center" }
        );
    }

    doc.save(`Swasthya-Sathi-Attendance-Report-${Date.now()}.pdf`);
}