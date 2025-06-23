เอกสารข้อกำหนดคุณสมบัติ (Requirement Specification)

**ชื่อโครงการ**: Mega Care Connect

**เวอร์ชัน**: 2.0

**วันที่ปรับปรุง**: 23 มิถุนายน 2568

**วัตถุประสงค์**: เพื่อระบุข้อกำหนดทางเทคนิคสำหรับแต่ละ Service ในสถาปัตยกรรมของโครงการ สำหรับส่งมอบให้ทีมพัฒนา (Programmer) นำไปพัฒนาต่อ

**ภาพรวมสถาปัตยกรรม**: ระบบประกอบด้วย LINE LIFF App สำหรับ User Interface, Backend APIs ที่ทำงานบน Cloud Run, ระบบดึงข้อมูลจาก ResMed AirView, และ Chatbot ที่ใช้ Langflow เป็นแกนประมวลผล ทั้งหมดทำงานบน Google Cloud Platform

---

## Service 1: LINE LIFF Frontend Application

**คำอธิบาย**: เป็น User Interface หลักของระบบในรูปแบบ Web Application ที่ทำงานอยู่ภายในแอปพลิเคชัน LINE เพื่อให้ผู้ใช้เข้าถึงข้อมูลและจัดการอุปกรณ์ของตนเอง

**Technology Stack**:

*   **Hosting**: Cloud Run (สำหรับให้บริการแอปพลิเคชัน Vue.js)
*   **Framework**: Vue.js
*   **Core Library**: LINE LIFF SDK
*   **UI Component**: Tailwind CSS

**Core Requirements**:

*   **Application Entry Flow (สำคัญ)**:
    *   เมื่อผู้ใช้เปิด LIFF App ครั้งแรก, แอปจะต้องเรียก API ของ Backend เพื่อตรวจสอบสถานะการเชื่อมต่อบัญชี (Account Link Status) ของ `lineId` ปัจจุบัน
    *   กรณียังไม่เชื่อมต่อ: ต้องแสดงผลเฉพาะ "หน้าเชื่อมต่อบัญชี (Account Linking Page)" เท่านั้น ส่วนของแอปพลิเคชันหลักและแถบเมนูด้านล่าง (Navigation Bar) จะต้องถูกซ่อนไว้
    *   กรณีเชื่อมต่อแล้ว: แสดงผลแอปพลิเคชันหลัก โดยเริ่มต้นที่ "หน้าแดชบอร์ด (Dashboard)"

*   **การยืนยันตัวตน (Authentication)**:
    *   ใช้ LIFF SDK เพื่อขอ `accessToken` จาก LINE
    *   ส่ง `accessToken` นี้ไปกับทุกๆ Request ที่เรียกไปยัง Backend API ผ่าน `Authorization` header (`Bearer <TOKEN>`)

*   **หน้าเชื่อมต่อบัญชี (Account Linking Page)**:
    *   เป็นหน้าบังคับสำหรับผู้ใช้ใหม่
    *   มีฟอร์มสำหรับกรอก CPAP Serial Number
    *   เมื่อผู้ใช้กดยืนยัน, LIFF App จะเรียก `POST /api/v1/users/link-account`
    *   หากสำเร็จ ให้แสดงผลแอปพลิเคชันหลัก (Dashboard)
    *   หากล้มเหลว (เช่น Serial Number ไม่ถูกต้อง) ให้แสดงข้อความผิดพลาด

*   **หน้าแดชบอร์ด (Dashboard)**:
    *   เป็นหน้าแรกหลังจากล็อกอินสำเร็จ
    *   แสดงข้อมูลสรุปของการใช้งานล่าสุด โดยเรียก `GET /api/v1/reports/latest`

*   **หน้ารายงานย้อนหลัง (Reports History)**:
    *   แสดงกราฟแนวโน้มและรายการรายงานย้อนหลัง โดยเรียก `GET /api/v1/reports?startDate=...&endDate=...`
    *   แต่ละรายการในลิสต์จะต้องสามารถกดได้ เพื่อนำทางผู้ใช้ไปยัง "หน้าวิเคราะห์ผลรายวัน" ของวันที่เลือก

*   **หน้าวิเคราะห์ผลรายวัน (Report Detail Page)**:
    *   เป็นหน้าที่แสดงผลเมื่อผู้ใช้กดเลือกรายงานจากหน้า Reports History
    *   ต้องมีปุ่มสำหรับย้อนกลับไปหน้ารายงานย้อนหลัง
    *   แสดงข้อมูลโดยเรียก `GET /api/v1/reports/{reportDate}`
    *   **ส่วนที่ 1**: ผลการอ่านข้อมูล: แสดงข้อมูลดิบที่ได้จาก Backend
    *   **ส่วนที่ 2**: ผลการแปรผล: แสดงการวิเคราะห์แต่ละหัวข้อ (Usage, Leak, AHI, etc.) โดยใช้ไอคอนและสี (เขียว/เหลือง/แดง) เพื่อบ่งบอกสถานะตามข้อมูลที่ได้จาก Backend
    *   **ส่วนที่ 3**: สรุปคำแนะนำ: แสดงการ์ดสรุปคำแนะนำโดยรวมที่ได้จาก Backend

*   **หน้าอุปกรณ์ของฉัน (My Equipment)**:
    *   แสดงรายการอุปกรณ์ของผู้ใช้ โดยเรียก `GET /api/v1/equipment`

**Dependencies**: Backend API Service (Service 2)

---

## Service 2: Backend API Service

**คำอธิบาย**: เป็นกลุ่มของ Microservices ที่ทำงานบน Cloud Run ทำหน้าที่เป็น Backend for Frontend (BFF) ให้กับ LIFF App และเป็นตัวกลางในการเข้าถึงข้อมูลใน Firestore

**Technology Stack**:

*   **Compute**: Cloud Run
*   **API Management**: Google API Gateway
*   **Language**: Python (FastAPI)
*   **Database**: Firestore

**General Requirements**:

*   **Authentication Middleware**: ทุก Endpoint ต้องมีการตรวจสอบ `accessToken` จาก LINE เพื่อยืนยันตัวตนและดึง `lineId` ของผู้ใช้มาใช้งาน

**API Endpoints**:

*   **Endpoint**: `POST /api/v1/users/link-account`
    *   **Description**: ใช้สำหรับผูก `lineId` กับ `patientId` โดยใช้ CPAP Serial Number
    *   **Request Body**: `{ "serialNumber": "..." }`
    *   **Logic**: ค้นหา device ที่มี `serialNumber` ตรงกันใน Sub-collection `devices` ทั้งหมด หากพบ ให้ดึง `patientId` ของเอกสารแม่ (`customer`) มา แล้วอัปเดตฟิลด์ `lineId` ของเอกสาร `customers/{patientId}` นั้น หากไม่พบหรือ Serial Number ถูกใช้ไปแล้ว ให้ trả về error

*   **Endpoint**: `GET /api/v1/users/status`
    *   **Description**: ตรวจสอบสถานะการเชื่อมต่อบัญชีของผู้ใช้ปัจจุบัน
    *   **Response**: `{ "isLinked": true/false }`

*   **Endpoint**: `GET /api/v1/reports/{reportDate}`
    *   **Description**: ดึงข้อมูลรายงานและผลวิเคราะห์สำหรับวันใดวันหนึ่ง
    *   **Response (Success)**: `200 OK` พร้อม JSON Object ที่มีโครงสร้างดังนี้:
        ```json
        {
          "rawData": { "...": "..." },
          "analysis": {
            "usage": { "status": "normal", "text": "...", "recommendation": "..." },
            "leak": { "status": "high", "text": "...", "recommendation": "..." }
          },
          "overallRecommendation": "สรุปคำแนะนำโดยรวม..."
        }
        ```
    *   **Logic**: Service จะดึงข้อมูลดิบจาก Firestore, นำไปประมวลผลตามเงื่อนไขทางธุรกิจเพื่อสร้างผลวิเคราะห์และคำแนะนำ, แล้วจึงส่งกลับไปให้ Frontend

*   (Endpoints อื่นๆ เช่น `GET /api/v1/reports/latest`, `GET /api/v1/equipment` ยังคงเดิม)

---

## Service 3: Data Ingestion Service

(ข้อกำหนดคงเดิม ไม่มีการเปลี่ยนแปลง)

**คำอธิบาย**: Service ที่ทำงานเป็นรอบตามเวลา เพื่อดึงข้อมูลใหม่ๆ จาก ResMed AirView API มาอัปเดตใน Firestore

**Technology Stack**: Cloud Run, Cloud Scheduler, Python

---

## Service 4: Report Transcription Service (ถ้ามี)

(ข้อกำหนดคงเดิม ไม่มีการเปลี่ยนแปลง)

**คำอธิบาย**: Service ที่จะทำงานเมื่อมีไฟล์รายงาน (เช่น PDF) ถูกอัปโหลดเข้ามายัง Cloud Storage เพื่อทำการสกัดข้อมูล (OCR) และบันทึกลง Firestore

**Technology Stack**: Cloud Run, Cloud Storage Trigger, Google Document AI

---

## Service 5: Chatbot Webhook Service

(ข้อกำหนดคงเดิม ไม่มีการเปลี่ยนแปลง)

**คำอธิบาย**: Service สำหรับรับ Webhook จาก LINE Messaging API และประมวลผลข้อความจากผู้ใช้ผ่าน Langflow

**Technology Stack**: Cloud Run, Python/Node.js, Langflow