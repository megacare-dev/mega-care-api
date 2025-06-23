# ขั้นตอนการพัฒนาแอปพลิเคชัน Mega Care Connect

## Phase 0: การวางแผนและเตรียมการ (Planning & Setup)

### ตั้งค่าโปรเจกต์ (Project Setup)
- สร้างโปรเจกต์ใหม่บน Google Cloud Platform (GCP)
- เปิดใช้งาน APIs ที่จำเป็นทั้งหมด: Cloud Run, API Gateway, Cloud Scheduler, Firestore, Secret Manager, Document AI (ถ้าใช้)
- ตั้งค่า Repository บน GitHub (หรือ Version Control อื่นๆ) โดยแบ่งเป็น 2 ส่วนหลัก:
  - `https://github.com/megacare-dev/mega-care-connect` (สำหรับ Vue.js)
  - `https://github.com/megacare-dev/mega-care-api` (สำหรับ Python/FastAPI)

### ออกแบบแผนงาน (Sprint Planning)
- นำ Requirements ของแต่ละ Service มาแตกเป็น Task ย่อยๆ (เช่น "สร้าง Endpoint `/api/v1/users/status`", "สร้างหน้า Dashboard UI")
- จัดลำดับความสำคัญของ Task และวางแผนการทำงานเป็นรอบ (Sprint) โดยแนะนำให้เริ่มจาก Backend ก่อน เพราะ Frontend ต้องรอ API

---

## Phase 1: การพัฒนา Backend (Backend Development - Service 2)
**เป้าหมาย:** สร้าง API ทั้งหมดให้พร้อมสำหรับให้ Frontend เรียกใช้งาน โดยมี Authentication, Business Logic, และโครงสร้างที่เหมาะสม

### 1. ตั้งค่าโปรเจกต์และโครงสร้าง (Project & Structure Setup)
- **Done:** สร้างโครงสร้างโปรเจกต์ FastAPI ที่แบ่งสัดส่วนชัดเจน (`routers`, `models`, `dependencies`, `core/config.py`)
- **Done:** ติดตั้ง Dependencies ที่จำเป็นและสร้างไฟล์ `requirements.txt`
- **Done:** ตั้งค่าการเชื่อมต่อกับ Firestore (`app/dependencies/database.py`) และการจัดการค่า Config (`app/core/config.py`) ที่พร้อมสำหรับ Secret Manager

### 2. การออกแบบ Model และ Schema (Data Modeling)
- **Done:** สร้าง Pydantic Models สำหรับ Request Bodies (`LinkAccountRequest`) และ Response Bodies (`UserStatusResponse`) ใน `app/models/user.py`
- **Done:** สร้าง Pydantic Models สำหรับ `ReportDetailResponse` ใน `app/models/report.py` โดยอ้างอิงโครงสร้างจาก `requirement.md` เพื่อให้ Frontend ได้ข้อมูลที่ถูกต้องและมีการทำ Validation ที่ฝั่ง Backend

### 3. พัฒนา Middleware และการยืนยันตัวตน (Authentication Middleware)
- **Done:** สร้าง FastAPI Dependency (`get_current_line_id`) ใน `app/dependencies/auth.py` เพื่อจัดการ Authentication
- **Logic Implemented:**
  - ใช้ `fastapi.security.HTTPBearer` เพื่อดึง `Authorization: Bearer <TOKEN>` จาก Header
  - ใช้ `httpx` เพื่อเรียกใช้ LINE API `https://api.line.me/oauth2/v2.1/verify` แบบ asynchronous เพื่อตรวจสอบ `accessToken`
  - หาก Token ถูกต้อง, ดึง `sub` (ซึ่งคือ `lineId`) จาก Response ของ LINE และส่งคืนค่า
  - จัดการ Error Cases (เช่น Token หมดอายุ, Token ไม่ถูกต้อง, Network error) โดย trả về `401 Unauthorized` หรือ `500 Internal Server Error` พร้อมรายละเอียดที่เหมาะสม
- **Done:** อัปเดต `app/routers/users.py` และ `tests/conftest.py` ให้ใช้ Dependency ใหม่นี้

### 4. พัฒนา API Endpoints (ตามลำดับความสำคัญ)
- **Done: `GET /api/v1/users/status`**:
  - **Logic:** รับ `lineId` จาก Middleware, ค้นหาเอกสารใน `customers` collection และ trả vềสถานะการเชื่อมต่อ
- **Done: `POST /api/v1/users/link-account`**:
  - **Logic:** ใช้ Collection Group Query เพื่อค้นหา `serialNumber`, ตรวจสอบ, และอัปเดต `lineId` ในเอกสาร `customer`
- **Done: `GET /api/v1/equipment`**:
  - **Logic:** รับ `lineId` จาก Middleware, ค้นหา `patientId` ที่ผูกกัน, แล้วดึงข้อมูลจาก Sub-collection `devices` ของลูกค้ารายนั้น
- **Done: `GET /api/v1/reports/latest`**:
  - **Logic:** คล้ายกับ `equipment`, แต่ดึงข้อมูลรายงานล่าสุดจาก Sub-collection `reports` โดยเรียงลำดับและจำกัดผลลัพธ์
- **Done: `GET /api/v1/reports/{reportDate}`**:
  - **Service Layer:** สร้าง Service แยก (`app/services/report_analyzer.py`) สำหรับจัดการ Business Logic
  - **Logic:**
    1. ดึงข้อมูลดิบ (`rawData`) จาก Firestore สำหรับวันที่ระบุ
    2. นำ `rawData` มาประมวลผลตามเงื่อนไขทางธุรกิจเพื่อสร้างส่วน `analysis` และ `overallRecommendation`
    3. ประกอบผลลัพธ์ทั้งหมดตาม Pydantic Model ที่ออกแบบไว้แล้ว

### 5. การ Deploy และตั้งค่าบน GCP (Deployment & GCP Setup)
- **Done:** เขียน `Dockerfile` ที่มีประสิทธิภาพสำหรับแอปพลิเคชัน FastAPI โดยใช้ Multi-stage build และ Non-root user
- **Done:** สร้าง `cloudbuild.yaml` เพื่อกำหนดขั้นตอน CI/CD Pipeline
- **Next:** ตั้งค่า CI/CD Trigger บน GCP และจัดการ Environment Variables ผ่าน Secret Manager เพื่อให้ระบบพร้อมสำหรับการ Deploy อัตโนมัติ

### 6. ตั้งค่า API Gateway
- สร้าง API Gateway Configuration (OpenAPI Spec) เพื่อกำหนด Route ทั้งหมด
- ชี้แต่ละ Route ไปยัง Cloud Run Service ที่ Deploy ไว้
- เปิดใช้งาน CORS เพื่อให้ LIFF App สามารถเรียกใช้งาน API ได้อย่างปลอดภัย

---

## Phase 2: การพัฒนา Frontend (Frontend Development - Service 1)
**เป้าหมาย:** สร้าง User Interface ทั้งหมดตามที่ออกแบบไว้ และเชื่อมต่อกับ Backend API

### ตั้งค่าโปรเจกต์ Vue.js
- สร้างโปรเจกต์ Vue.js ด้วย `create-vue`
- ติดตั้ง Tailwind CSS และ LINE LIFF SDK

### พัฒนาส่วนจัดการสถานะและ API (State Management & API Layer)
- สร้าง Service สำหรับเรียกใช้งาน Backend API (เช่น ใช้ `axios`) โดยมีการแนบ `accessToken` จาก LIFF SDK ไปด้วยเสมอ
- ตั้งค่า State Management (เช่น Pinia) เพื่อเก็บข้อมูลผู้ใช้และสถานะการล็อกอิน

### พัฒนาหน้าจอ (Page Development)
- **หน้าเชื่อมต่อบัญชี (Account Linking Page):** สร้าง UI และ Logic การเรียก API `link-account`
- **Application Entry Flow:** พัฒนา Logic หลักที่หน้าแรกของแอป เพื่อเรียก `GET /api/v1/users/status` แล้วเลือกว่าจะแสดงหน้าเชื่อมต่อบัญชี หรือแอปพลิเคชันหลัก
- **หน้าจอหลัก (Dashboard, Reports, Equipment):** สร้าง UI ของแต่ละหน้า และเชื่อมต่อกับ API ที่สร้างไว้แล้ว
- **หน้าวิเคราะห์ผลรายวัน (Report Detail Page):** สร้าง UI สำหรับแสดงผลข้อมูลดิบ, ผลวิเคราะห์, และคำแนะนำตามโครงสร้าง JSON ที่ได้รับจาก Backend

### Deploy ขึ้น Cloud Run
- เขียน `Dockerfile` สำหรับ Vue.js (อาจใช้ Web Server อย่าง Nginx เพื่อ Serve Static Files)
- ตั้งค่า CI/CD Pipeline เพื่อ Build และ Deploy ไปยัง Cloud Run

---

## Phase 3: การพัฒนาระบบเบื้องหลัง (Background Services)
**เป้าหมาย:** ทำให้ระบบสามารถดึงข้อมูลและประมวลผลได้โดยอัตโนมัติ

### Data Ingestion Service (Service 3)
- สร้าง Cloud Run Service ใหม่สำหรับดึงข้อมูลจาก ResMed AirView API
- เขียน Logic การดึงและแปลงข้อมูลตาม Requirement
- ตั้งค่า Cloud Scheduler ให้ Trigger Service นี้ตามเวลาที่กำหนด

### Chatbot Service (Service 5)
- สร้าง Cloud Run Service สำหรับเป็น Webhook ของ LINE Messaging API
- พัฒนา Logic การรับข้อความและส่งต่อไปยัง Langflow
- ลงทะเบียน Webhook URL ใน LINE Developer Console

---

## Phase 4: การทดสอบและปรับปรุง (Testing & Refinement)
- **Integration Testing:** ทดสอบการทำงานร่วมกันของ Frontend และ Backend ว่าราบรื่นดีหรือไม่
- **End-to-End Testing:** ทดสอบ Flow ทั้งหมด ตั้งแต่การเปิด LIFF App ครั้งแรก, เชื่อมต่อบัญชี, ไปจนถึงการดูหน้ารายละเอียด
- **User Acceptance Test (UAT):** ให้ผู้ใช้งานจริงหรือทีมงานที่เกี่ยวข้องทดลองใช้และเก็บ Feedback เพื่อนำมาปรับปรุง
- **Go-Live:** เมื่อทุกอย่างพร้อม ก็สามารถเปิดให้ผู้ใช้งานทั่วไปใช้งานได้