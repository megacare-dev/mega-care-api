# ขั้นตอนการพัฒนาแอปพลิเคชัน Mega Care Connect

## Phase 1: การพัฒนา Backend (Backend Development - Service 2)
**เป้าหมาย:** สร้าง API ทั้งหมดให้พร้อมสำหรับให้ Frontend เรียกใช้งาน โดยมี Authentication, Business Logic, และโครงสร้างที่เหมาะสม ตามแนวทาง Test-Driven Development (TDD)

## หลักการ TDD: Red-Green-Refactor
สำหรับทุกฟีเจอร์หรือ Endpoint ที่จะพัฒนา ให้ทำตามวงจรนี้อย่างเคร่งครัด:
1.  **RED:** เขียน Unit Test ที่คาดว่าจะล้มเหลว (Failing Test) เพราะยังไม่มีโค้ดจริงมารองรับ
2.  **GREEN:** เขียนโค้ด Production เพียงเท่าที่จำเป็น เพื่อทำให้ Test ที่ล้มเหลวกลับมา "ผ่าน"
3.  **REFACTOR:** ปรับปรุงโค้ด Production และ Test ให้สะอาด มีคุณภาพ โดยที่ Test ทั้งหมดยังคง "ผ่าน"

---

## ขั้นตอนการพัฒนา

### 1. ตั้งค่าโปรเจกต์และโครงสร้าง (Project & Structure Setup)
-   **Done:** สร้างโครงสร้างโปรเจกต์ FastAPI ที่แบ่งสัดส่วนชัดเจน (`routers`, `models`, `dependencies`, `core/config.py`)
-   **Done:** ติดตั้ง Dependencies ที่จำเป็นและสร้างไฟล์ `requirements.txt`
-   **Done:** ตั้งค่าการเชื่อมต่อกับ Firestore (`app/dependencies/database.py`) และการจัดการค่า Config (`app/core/config.py`) ที่พร้อมสำหรับ Secret Manager

### 2. การออกแบบ Model และ Schema (Data Modeling)
-   **Done:** สร้าง Pydantic Models สำหรับ Request Bodies (`LinkAccountRequest`) และ Response Bodies (`UserStatusResponse`) ใน `app/models/user.py`
-   **Done:** สร้าง Pydantic Models สำหรับ `ReportDetailResponse` ใน `app/models/report.py` โดยอ้างอิงโครงสร้างจาก `requirement.md` เพื่อให้ Frontend ได้ข้อมูลที่ถูกต้องและมีการทำ Validation ที่ฝั่ง Backend

### 3. พัฒนา Middleware และการยืนยันตัวตน (Authentication Middleware)
-   **Done:** สร้าง FastAPI Dependency (`get_current_line_id`) ใน `app/dependencies/auth.py` เพื่อจัดการ Authentication
    -   **Done (RED):** เขียน Unit Test สำหรับ `_verify_line_token` (ใน `app/dependencies/auth.py`) เพื่อทดสอบกรณี Token ถูกต้อง, Token ไม่ถูกต้อง, และ Token Payload ไม่สมบูรณ์ (เช่น ไม่มี `sub`)
    -   **Done (GREEN):** Implement Logic ใน `_verify_line_token` โดยใช้ `httpx` เพื่อเรียก LINE API `https://api.line.me/oauth2/v2.1/verify` และจัดการ Error Cases
    -   **Done (REFACTOR):** ปรับปรุงโค้ด `_verify_line_token` ให้สะอาดและมีประสิทธิภาพ
-   **Done:** อัปเดต `app/routers/users.py` และ `tests/conftest.py` ให้ใช้ Dependency ใหม่นี้

### 4. พัฒนา API Endpoints (ตามลำดับความสำคัญ)

#### 4.1. `GET /api/v1/users/status`
-   **Done (RED):**
    -   เขียน Unit Test ใน `tests/test_users.py` เพื่อทดสอบ Endpoint `/api/v1/users/status`
    -   Test Case: ผู้ใช้เชื่อมต่อบัญชีแล้ว (คาดหวัง `{"isLinked": true}`)
    -   Test Case: ผู้ใช้ยังไม่เชื่อมต่อบัญชี (คาดหวัง `{"isLinked": false}`)
    -   รัน Test และยืนยันว่าล้มเหลว (เช่น 404 Not Found หรือ 500 Internal Server Error)
-   **Done (GREEN):**
    -   สร้าง Endpoint `GET /api/v1/users/status` ใน `app/routers/users.py`
    -   Implement Logic เพื่อรับ `lineId` จาก Middleware, ค้นหาเอกสารใน `customers` collection และ trả กลับสถานะการเชื่อมต่อ
    -   รัน Test อีกครั้งและยืนยันว่า Test ผ่านทั้งหมด
-   **Done (REFACTOR):**
    -   ปรับปรุงโค้ดใน Endpoint ให้สะอาด, อ่านง่าย, และมีประสิทธิภาพ
    -   รัน Test ทั้งหมดอีกครั้งเพื่อยืนยันว่ายังคงผ่าน

#### 4.2. `POST /api/v1/users/link-account`
-   **Done (RED):**
    -   เขียน Unit Test ใน `tests/test_users.py` เพื่อทดสอบ Endpoint `POST /api/v1/users/link-account`
    -   Test Case: Serial Number ถูกต้องและยังไม่ถูกผูก (คาดหวัง 204 No Content และมีการอัปเดต `lineId` ใน Firestore)
    -   Test Case: Serial Number ไม่พบ (คาดหวัง 404 Not Found) และอุปกรณ์ถูกผูกแล้ว (คาดหวัง 409 Conflict)
    -   รัน Test และยืนยันว่าล้มเหลว
-   **Done (GREEN):**
    -   สร้าง Endpoint `POST /api/v1/users/link-account` ใน `app/routers/users.py`
    -   Implement Logic โดยใช้ Collection Group Query เพื่อค้นหา `serialNumber`, ตรวจสอบ, และอัปเดต `lineId` ในเอกสาร `customer`
    -   รัน Test อีกครั้งและยืนยันว่า Test ผ่านทั้งหมด
-   **Done (REFACTOR):**
    -   ปรับปรุงโค้ดใน Endpoint ให้สะอาด, อ่านง่าย, และมีประสิทธิภาพ
    -   รัน Test ทั้งหมดอีกครั้งเพื่อยืนยันว่ายังคงผ่าน

#### 4.3. `GET /api/v1/equipment`
-   **Done (RED):**
    -   เขียน Unit Test ใน `tests/test_equipment.py` เพื่อทดสอบ Endpoint `GET /api/v1/equipment`
    -   Test Case: ผู้ใช้มีอุปกรณ์ (คาดหวัง 200 OK พร้อมรายการอุปกรณ์)
    -   Test Case: ผู้ใช้ไม่มีอุปกรณ์ (คาดหวัง 200 OK พร้อมรายการว่าง)
    -   Test Case: ผู้ใช้ยังไม่เชื่อมต่อบัญชี (คาดหวัง 404 Not Found หรือ 401 Unauthorized หาก `get_current_line_id` ไม่ได้จัดการ)
    -   รัน Test และยืนยันว่าล้มเหลว
-   **Done (GREEN):**
    -   สร้าง Endpoint `GET /api/v1/equipment` ใน `app/routers/equipment.py`
    -   Implement Logic เพื่อรับ `lineId` จาก Middleware, ค้นหา `patientId` ที่ผูกกัน, แล้วดึงข้อมูลจาก Sub-collection `devices` ของลูกค้ารายนั้น
    -   รัน Test อีกครั้งและยืนยันว่า Test ผ่านทั้งหมด
-   **Done (REFACTOR):**
    -   ปรับปรุงโค้ดใน Endpoint ให้สะอาด, อ่านง่าย, และมีประสิทธิภาพ
    -   รัน Test ทั้งหมดอีกครั้งเพื่อยืนยันว่ายังคงผ่าน

#### 4.4. `GET /api/v1/reports/latest`
-   **Done (RED):**
    -   เขียน Unit Test ใน `tests/test_reports.py` เพื่อทดสอบ Endpoint `GET /api/v1/reports/latest`
    -   Test Case: ผู้ใช้มีรายงานล่าสุด (คาดหวัง 200 OK พร้อมข้อมูลรายงาน)
    -   Test Case: ผู้ใช้ไม่มีรายงาน (คาดหวัง 404 Not Found)
    -   รัน Test และยืนยันว่าล้มเหลว
-   **Done (GREEN):**
    -   สร้าง Endpoint `GET /api/v1/reports/latest` ใน `app/routers/reports.py`
    -   Implement Logic เพื่อดึงข้อมูลรายงานล่าสุดจาก Sub-collection `dailyReports` โดยเรียงลำดับและจำกัดผลลัพธ์
    -   รัน Test อีกครั้งและยืนยันว่า Test ผ่านทั้งหมด
-   **Done (REFACTOR):**
    -   ปรับปรุงโค้ดใน Endpoint ให้สะอาด, อ่านง่าย, และมีประสิทธิภาพ
    -   รัน Test ทั้งหมดอีกครั้งเพื่อยืนยันว่ายังคงผ่าน

#### 4.5. `GET /api/v1/reports/{reportDate}`
-   **Done (RED):**
    -   เขียน Unit Test ใน `tests/test_reports.py` เพื่อทดสอบ Endpoint `GET /api/v1/reports/{reportDate}`
    -   Test Case: มีรายงานสำหรับวันที่ระบุ (คาดหวัง 200 OK พร้อมข้อมูลรายงาน, analysis, และ overallRecommendation)
    -   Test Case: ไม่มีรายงานสำหรับวันที่ระบุ (คาดหวัง 404 Not Found)
    -   รัน Test และยืนยันว่าล้มเหลว
-   **Done (GREEN):**
    -   สร้าง Service แยก (`app/services/report_analyzer.py`) สำหรับจัดการ Business Logic การวิเคราะห์รายงาน
    -   สร้าง Endpoint `GET /api/v1/reports/{reportDate}` ใน `app/routers/reports.py`
    -   Implement Logic: ดึงข้อมูลดิบ (`rawData`) จาก Firestore, นำไปประมวลผลผ่าน `report_analyzer.py` เพื่อสร้างส่วน `analysis` และ `overallRecommendation`, แล้วประกอบผลลัพธ์ทั้งหมดตาม Pydantic Model
    -   รัน Test อีกครั้งและยืนยันว่า Test ผ่านทั้งหมด
-   **Done (REFACTOR):**
    -   ปรับปรุงโค้ดใน Endpoint และ `report_analyzer.py` ให้สะอาด, อ่านง่าย, และมีประสิทธิภาพ
    -   รัน Test ทั้งหมดอีกครั้งเพื่อยืนยันว่ายังคงผ่าน

### 5. การ Deploy และตั้งค่าบน GCP (Deployment & GCP Setup)
-   **Done:** เขียน `Dockerfile` ที่มีประสิทธิภาพสำหรับแอปพลิเคชัน FastAPI โดยใช้ Multi-stage build และ Non-root user
-   **Done:** สร้าง `cloudbuild.yaml` เพื่อกำหนดขั้นตอน CI/CD Pipeline
-   **Done:** จัดการ Environment Variables ผ่าน Secret Manager ใน `cloudbuild.yaml`
-   **Done:** ตั้งค่า CI/CD Trigger บน GCP เพื่อเชื่อมต่อกับ Git Repository และเริ่มการ Deploy อัตโนมัติ

### 6. ตั้งค่า API Gateway
-   **Next:** สร้าง API Gateway Configuration (OpenAPI Spec) เพื่อกำหนด Route ทั้งหมด
-   **Next:** ชี้แต่ละ Route ไปยัง Cloud Run Service ที่ Deploy ไว้
-   **Next:** เปิดใช้งาน CORS เพื่อให้ LIFF App สามารถเรียกใช้งาน API ได้อย่างปลอดภัย