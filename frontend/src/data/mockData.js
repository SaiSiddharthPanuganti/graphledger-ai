export const MISMATCHES = [
  {id:"MIS-001",invoice_no:"INV-0042",supplier_gstin:"27AABCM1234F1Z5",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"IRN_MISMATCH",gstr1_value:285000,gstr2b_value:0,itc_at_risk:51300,period:"102024",risk_level:"CRITICAL",status:"PENDING",root_cause:"IRN not found on IRP portal"},
  {id:"MIS-002",invoice_no:"INV-0078",supplier_gstin:"07AAFCS9876K1Z3",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"AMOUNT_MISMATCH",gstr1_value:142000,gstr2b_value:118000,itc_at_risk:4320,period:"092024",risk_level:"HIGH",status:"IN_PROGRESS",root_cause:"Supplier filed amendment in GSTR-1A"},
  {id:"MIS-003",invoice_no:"INV-0091",supplier_gstin:"24AAACG8765H1Z7",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"INVOICE_MISSING_2B",gstr1_value:98500,gstr2b_value:0,itc_at_risk:17730,period:"082024",risk_level:"HIGH",status:"PENDING",root_cause:"Supplier GSTR-1 not filed for August 2024"},
  {id:"MIS-004",invoice_no:"INV-0123",supplier_gstin:"33AAECS3456J1Z1",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"DATE_MISMATCH",gstr1_value:75000,gstr2b_value:75000,itc_at_risk:13500,period:"102024",risk_level:"MEDIUM",status:"IN_PROGRESS",root_cause:"Invoice date Oct, booked in Nov GSTR-3B"},
  {id:"MIS-005",invoice_no:"INV-0156",supplier_gstin:"09AAACJ6543M1Z9",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"EWAYBILL_MISSING",gstr1_value:620000,gstr2b_value:620000,itc_at_risk:111600,period:"112024",risk_level:"CRITICAL",status:"PENDING",root_cause:"Goods value above ₹50k threshold, EWB not generated"},
  {id:"MIS-006",invoice_no:"INV-0188",supplier_gstin:"29AAACG2345N1Z2",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"GSTIN_MISMATCH",gstr1_value:45000,gstr2b_value:45000,itc_at_risk:8100,period:"092024",risk_level:"HIGH",status:"RESOLVED",root_cause:"Wrong GSTIN captured at point of purchase"},
  {id:"MIS-007",invoice_no:"INV-0201",supplier_gstin:"07AAFCS9876K1Z3",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"EXTRA_IN_2B",gstr1_value:0,gstr2b_value:55000,itc_at_risk:9900,period:"072024",risk_level:"MEDIUM",status:"IN_PROGRESS",root_cause:"Supplier uploaded duplicate invoice to GSTR-1"},
  {id:"MIS-008",invoice_no:"INV-0234",supplier_gstin:"24AAACG8765H1Z7",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"IRN_MISMATCH",gstr1_value:890000,gstr2b_value:890000,itc_at_risk:160200,period:"112024",risk_level:"CRITICAL",status:"PENDING",root_cause:"IRN cryptographic signature tampered"},
  {id:"MIS-009",invoice_no:"INV-0267",supplier_gstin:"07AAACL4567P1Z6",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"AMOUNT_MISMATCH",gstr1_value:330000,gstr2b_value:295000,itc_at_risk:6300,period:"082024",risk_level:"MEDIUM",status:"PENDING",root_cause:"CGST/SGST split incorrectly reported"},
  {id:"MIS-010",invoice_no:"INV-0299",supplier_gstin:"33AAECS3456J1Z1",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"INVOICE_MISSING_2B",gstr1_value:178000,gstr2b_value:0,itc_at_risk:32040,period:"102024",risk_level:"HIGH",status:"IN_PROGRESS",root_cause:"Supplier filed nil GSTR-1 despite having sales"},
  {id:"MIS-011",invoice_no:"INV-0312",supplier_gstin:"27AABCM1234F1Z5",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"AMOUNT_MISMATCH",gstr1_value:560000,gstr2b_value:498000,itc_at_risk:11160,period:"072024",risk_level:"HIGH",status:"PENDING",root_cause:"Supplier revised invoice value post-supply"},
  {id:"MIS-012",invoice_no:"INV-0348",supplier_gstin:"09AAACJ6543M1Z9",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"IRN_MISMATCH",gstr1_value:412000,gstr2b_value:0,itc_at_risk:74160,period:"062024",risk_level:"CRITICAL",status:"PENDING",root_cause:"Duplicate IRN detected — possible invoice fraud"},
  {id:"MIS-013",invoice_no:"INV-0367",supplier_gstin:"29AAACG2345N1Z2",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"DATE_MISMATCH",gstr1_value:89000,gstr2b_value:89000,itc_at_risk:16020,period:"092024",risk_level:"MEDIUM",status:"RESOLVED",root_cause:"Invoice dated Sep, filed in Oct GSTR-1"},
  {id:"MIS-014",invoice_no:"INV-0389",supplier_gstin:"24AAACG8765H1Z7",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"INVOICE_MISSING_2B",gstr1_value:245000,gstr2b_value:0,itc_at_risk:44100,period:"072024",risk_level:"HIGH",status:"PENDING",root_cause:"Gujarat Agro missed GSTR-1 filing for Jul 2024"},
  {id:"MIS-015",invoice_no:"INV-0401",supplier_gstin:"07AAFCS9876K1Z3",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"EWAYBILL_MISSING",gstr1_value:780000,gstr2b_value:780000,itc_at_risk:140400,period:"112024",risk_level:"CRITICAL",status:"PENDING",root_cause:"Interstate goods movement without EWB"},
  {id:"MIS-016",invoice_no:"INV-0423",supplier_gstin:"33AAECS3456J1Z1",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"GSTIN_MISMATCH",gstr1_value:67000,gstr2b_value:67000,itc_at_risk:12060,period:"082024",risk_level:"HIGH",status:"IN_PROGRESS",root_cause:"Supplier used old GSTIN before amendment"},
  {id:"MIS-017",invoice_no:"INV-0445",supplier_gstin:"27AABCM1234F1Z5",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"EXTRA_IN_2B",gstr1_value:0,gstr2b_value:125000,itc_at_risk:22500,period:"062024",risk_level:"MEDIUM",status:"PENDING",root_cause:"Invoice in 2B with no purchase record"},
  {id:"MIS-018",invoice_no:"INV-0467",supplier_gstin:"07AAACL4567P1Z6",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"AMOUNT_MISMATCH",gstr1_value:195000,gstr2b_value:172000,itc_at_risk:4140,period:"112024",risk_level:"MEDIUM",status:"IN_PROGRESS",root_cause:"Freight charges included in GSTR-1 but not in PO"},
  {id:"MIS-019",invoice_no:"INV-0489",supplier_gstin:"09AAACJ6543M1Z9",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"INVOICE_MISSING_2B",gstr1_value:320000,gstr2b_value:0,itc_at_risk:57600,period:"062024",risk_level:"HIGH",status:"PENDING",root_cause:"Supplier suspended — all filings blocked by GSTN"},
  {id:"MIS-020",invoice_no:"INV-0512",supplier_gstin:"24AAACG8765H1Z7",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"IRN_MISMATCH",gstr1_value:1150000,gstr2b_value:1150000,itc_at_risk:207000,period:"052024",risk_level:"CRITICAL",status:"PENDING",root_cause:"IRN generated on cancelled e-invoice"},
  {id:"MIS-021",invoice_no:"INV-0534",supplier_gstin:"29AAACG2345N1Z2",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"DATE_MISMATCH",gstr1_value:54000,gstr2b_value:54000,itc_at_risk:9720,period:"052024",risk_level:"MEDIUM",status:"RESOLVED",root_cause:"Tax period straddles financial year boundary"},
  {id:"MIS-022",invoice_no:"INV-0556",supplier_gstin:"07AAFCS9876K1Z3",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"AMOUNT_MISMATCH",gstr1_value:438000,gstr2b_value:410000,itc_at_risk:5040,period:"052024",risk_level:"HIGH",status:"IN_PROGRESS",root_cause:"Discount applied post-supply not reflected in GSTR-1"},
  {id:"MIS-023",invoice_no:"INV-0578",supplier_gstin:"33AAECS3456J1Z1",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"EWAYBILL_MISSING",gstr1_value:510000,gstr2b_value:510000,itc_at_risk:91800,period:"042024",risk_level:"CRITICAL",status:"PENDING",root_cause:"Vehicle breakdown mid-route, EWB extension not done"},
  {id:"MIS-024",invoice_no:"INV-0601",supplier_gstin:"27AABCM1234F1Z5",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"GSTIN_MISMATCH",gstr1_value:92000,gstr2b_value:92000,itc_at_risk:16560,period:"042024",risk_level:"HIGH",status:"PENDING",root_cause:"Supplier used branch GSTIN instead of HO GSTIN"},
  {id:"MIS-025",invoice_no:"INV-0623",supplier_gstin:"07AAACL4567P1Z6",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"INVOICE_MISSING_2B",gstr1_value:143000,gstr2b_value:0,itc_at_risk:25740,period:"032024",risk_level:"HIGH",status:"IN_PROGRESS",root_cause:"Portal technical error — GSTR-1 upload failed"},
  {id:"MIS-026",invoice_no:"INV-0645",supplier_gstin:"09AAACJ6543M1Z9",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"EXTRA_IN_2B",gstr1_value:0,gstr2b_value:88000,itc_at_risk:15840,period:"032024",risk_level:"MEDIUM",status:"PENDING",root_cause:"Cancelled invoice re-uploaded by supplier by mistake"},
  {id:"MIS-027",invoice_no:"INV-0668",supplier_gstin:"24AAACG8765H1Z7",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"AMOUNT_MISMATCH",gstr1_value:267000,gstr2b_value:241000,itc_at_risk:4680,period:"022024",risk_level:"MEDIUM",status:"RESOLVED",root_cause:"Packing charges billed separately but GST filed together"},
  {id:"MIS-028",invoice_no:"INV-0689",supplier_gstin:"29AAACG2345N1Z2",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"IRN_MISMATCH",gstr1_value:375000,gstr2b_value:0,itc_at_risk:67500,period:"022024",risk_level:"CRITICAL",status:"PENDING",root_cause:"IRP portal outage — IRN ack not received"},
  {id:"MIS-029",invoice_no:"INV-0712",supplier_gstin:"07AAFCS9876K1Z3",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"DATE_MISMATCH",gstr1_value:110000,gstr2b_value:110000,itc_at_risk:19800,period:"012024",risk_level:"MEDIUM",status:"IN_PROGRESS",root_cause:"Invoice raised on 31-Jan but filed in Feb GSTR-1"},
  {id:"MIS-030",invoice_no:"INV-0734",supplier_gstin:"33AAECS3456J1Z1",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"INVOICE_MISSING_2B",gstr1_value:490000,gstr2b_value:0,itc_at_risk:88200,period:"012024",risk_level:"HIGH",status:"PENDING",root_cause:"Supplier filed GSTR-1 after 2B generation cutoff"},
  {id:"MIS-031",invoice_no:"INV-0756",supplier_gstin:"27AABCM1234F1Z5",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"EWAYBILL_MISSING",gstr1_value:840000,gstr2b_value:840000,itc_at_risk:151200,period:"122023",risk_level:"CRITICAL",status:"PENDING",root_cause:"EWB expired during transit, not renewed"},
  {id:"MIS-032",invoice_no:"INV-0778",supplier_gstin:"24AAACG8765H1Z7",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"AMOUNT_MISMATCH",gstr1_value:198000,gstr2b_value:165000,itc_at_risk:5940,period:"122023",risk_level:"HIGH",status:"IN_PROGRESS",root_cause:"GST rate changed 18% to 12% — not updated by supplier"},
  {id:"MIS-033",invoice_no:"INV-0801",supplier_gstin:"09AAACJ6543M1Z9",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"GSTIN_MISMATCH",gstr1_value:72000,gstr2b_value:72000,itc_at_risk:12960,period:"112023",risk_level:"HIGH",status:"RESOLVED",root_cause:"New state registration used on old invoice template"},
  {id:"MIS-034",invoice_no:"INV-0823",supplier_gstin:"07AAACL4567P1Z6",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"EXTRA_IN_2B",gstr1_value:0,gstr2b_value:43000,itc_at_risk:7740,period:"102023",risk_level:"MEDIUM",status:"PENDING",root_cause:"Debit note uploaded as invoice in GSTR-1"},
  {id:"MIS-035",invoice_no:"INV-0845",supplier_gstin:"29AAACG2345N1Z2",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"IRN_MISMATCH",gstr1_value:655000,gstr2b_value:0,itc_at_risk:117900,period:"092023",risk_level:"CRITICAL",status:"PENDING",root_cause:"IRN generated for cancelled invoice — system error"},
  {id:"MIS-036",invoice_no:"INV-0867",supplier_gstin:"07AAFCS9876K1Z3",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"INVOICE_MISSING_2B",gstr1_value:387000,gstr2b_value:0,itc_at_risk:69660,period:"082023",risk_level:"HIGH",status:"IN_PROGRESS",root_cause:"Supplier GSTIN cancelled — filings auto-blocked"},
  {id:"MIS-037",invoice_no:"INV-0889",supplier_gstin:"33AAECS3456J1Z1",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"DATE_MISMATCH",gstr1_value:134000,gstr2b_value:134000,itc_at_risk:24120,period:"072023",risk_level:"MEDIUM",status:"RESOLVED",root_cause:"Advance payment invoice vs supply invoice period mismatch"},
  {id:"MIS-038",invoice_no:"INV-0912",supplier_gstin:"27AABCM1234F1Z5",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"AMOUNT_MISMATCH",gstr1_value:920000,gstr2b_value:875000,itc_at_risk:8100,period:"062023",risk_level:"HIGH",status:"PENDING",root_cause:"Service charge taxable component disputed"},
  {id:"MIS-039",invoice_no:"INV-0934",supplier_gstin:"24AAACG8765H1Z7",buyer_gstin:"27AABCM1234F1Z5",mismatch_type:"EWAYBILL_MISSING",gstr1_value:695000,gstr2b_value:695000,itc_at_risk:125100,period:"052023",risk_level:"CRITICAL",status:"PENDING",root_cause:"Multi-modal transport EWB not updated at handoff"},
  {id:"MIS-040",invoice_no:"INV-0956",supplier_gstin:"09AAACJ6543M1Z9",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"INVOICE_MISSING_2B",gstr1_value:223000,gstr2b_value:0,itc_at_risk:40140,period:"042023",risk_level:"HIGH",status:"IN_PROGRESS",root_cause:"Supplier under GST audit — all filings frozen"},
  {id:"MIS-041",invoice_no:"INV-1101",supplier_gstin:"27AABCM1234F1Z5",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"PAYMENT_OVERDUE_180_DAYS",gstr1_value:540000,gstr2b_value:540000,itc_at_risk:97200,period:"082023",risk_level:"CRITICAL",status:"PENDING",root_cause:"Invoice unpaid for 215 days — ITC reversal mandatory under Sec 16(2)(b)"},
  {id:"MIS-042",invoice_no:"INV-1145",supplier_gstin:"07AAFCS9876K1Z3",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"PAYMENT_OVERDUE_180_DAYS",gstr1_value:312000,gstr2b_value:312000,itc_at_risk:56160,period:"092023",risk_level:"CRITICAL",status:"PENDING",root_cause:"Invoice unpaid for 198 days — ITC reversal mandatory under Sec 16(2)(b)"},
  {id:"MIS-043",invoice_no:"INV-1187",supplier_gstin:"24AAACG8765H1Z7",buyer_gstin:"29AADCV5678B1ZP",mismatch_type:"PAYMENT_OVERDUE_180_DAYS",gstr1_value:175000,gstr2b_value:175000,itc_at_risk:31500,period:"102023",risk_level:"HIGH",status:"PENDING",root_cause:"Paid after 195 days — late; ITC reversal + interest required"}
];

export const VENDORS = [
  {name:"Mahindra Castings Pvt Ltd",gstin:"27AABCM1234F1Z5",sector:"Manufacturing",state:"Maharashtra",risk_score:82,risk_category:"CRITICAL",mismatch_count:8,itc_at_risk:185400,filing_streak:2,rec:"Restrict ITC. Initiate vendor audit."},
  {name:"Flex Systems India",gstin:"07AAFCS9876K1Z3",sector:"Services",state:"Delhi",risk_score:67,risk_category:"HIGH",mismatch_count:5,itc_at_risk:94500,filing_streak:7,rec:"Enhanced monitoring required."},
  {name:"Gujarat Agro Chemicals",gstin:"24AAACG8765H1Z7",sector:"Manufacturing",state:"Gujarat",risk_score:71,risk_category:"HIGH",mismatch_count:6,itc_at_risk:210300,filing_streak:4,rec:"Request compliance certificate."},
  {name:"Chennai Electrical Co",gstin:"33AAECS3456J1Z1",sector:"Trading",state:"Tamil Nadu",risk_score:55,risk_category:"MEDIUM",mismatch_count:3,itc_at_risk:45600,filing_streak:11,rec:"Quarterly review. Watch list."},
  {name:"Jain Logistics UP",gstin:"09AAACJ6543M1Z9",sector:"Services",state:"Uttar Pradesh",risk_score:78,risk_category:"HIGH",mismatch_count:4,itc_at_risk:123900,filing_streak:5,rec:"Enhanced monitoring required."},
  {name:"Bangalore Auto Parts",gstin:"29AAACG2345N1Z2",sector:"Manufacturing",state:"Karnataka",risk_score:44,risk_category:"MEDIUM",mismatch_count:2,itc_at_risk:28700,filing_streak:16,rec:"Quarterly review."},
  {name:"Delhi Cloud Tech",gstin:"07AAACL4567P1Z6",sector:"Services",state:"Delhi",risk_score:31,risk_category:"LOW",mismatch_count:1,itc_at_risk:6300,filing_streak:22,rec:"Standard processing. Annual review."},
  {name:"ACME Exports Ltd",gstin:"29AADCV5678B1ZP",sector:"Export",state:"Karnataka",risk_score:22,risk_category:"LOW",mismatch_count:0,itc_at_risk:0,filing_streak:24,rec:"No action required."}
];

export const MISMATCH_TYPE_BREAKDOWN = [
  {type:"AMOUNT_MISMATCH",count:53,itc_at_risk:285000,risk_level:"HIGH"},
  {type:"INVOICE_MISSING_2B",count:37,itc_at_risk:412000,risk_level:"HIGH"},
  {type:"EXTRA_IN_2B",count:15,itc_at_risk:89000,risk_level:"MEDIUM"},
  {type:"GSTIN_MISMATCH",count:15,itc_at_risk:121500,risk_level:"HIGH"},
  {type:"DATE_MISMATCH",count:15,itc_at_risk:67500,risk_level:"MEDIUM"},
  {type:"IRN_MISMATCH",count:7,itc_at_risk:380700,risk_level:"CRITICAL"},
  {type:"EWAYBILL_MISSING",count:8,itc_at_risk:289600,risk_level:"CRITICAL"},
  {type:"PAYMENT_OVERDUE_180_DAYS",count:9,itc_at_risk:184860,risk_level:"CRITICAL"}
];

// Section 16(2)(b) CGST Act — 180-Day Payment Compliance data
export const PAYMENT_OVERDUE = [
  {invoice_id:"pay-1101",invoice_no:"INV-1101",supplier_name:"Mahindra Castings Pvt Ltd",supplier_gstin:"27AABCM1234F1Z5",invoice_date:"2024-01-15",days_old:215,itc_value:97200,interest_liability:10422,payment_status:"UNPAID_OVERDUE",days_left:0,action:"Reverse ITC in GSTR-3B Table 4(B)(2) immediately"},
  {invoice_id:"pay-1145",invoice_no:"INV-1145",supplier_name:"Flex Systems India",supplier_gstin:"07AAFCS9876K1Z3",invoice_date:"2024-02-01",days_old:198,itc_value:56160,interest_liability:5521,payment_status:"UNPAID_OVERDUE",days_left:0,action:"Reverse ITC in GSTR-3B Table 4(B)(2) immediately"},
  {invoice_id:"pay-1187",invoice_no:"INV-1187",supplier_name:"Gujarat Agro Chemicals",supplier_gstin:"24AAACG8765H1Z7",invoice_date:"2024-02-20",days_old:179,itc_value:31500,interest_liability:2790,payment_status:"UNPAID_OVERDUE",days_left:0,action:"Reverse ITC — paid after 195 days, interest due under Sec 50(3)"},
  {invoice_id:"pay-1203",invoice_no:"INV-1203",supplier_name:"Chennai Electrical Co",supplier_gstin:"33AAECS3456J1Z1",invoice_date:"2024-03-10",days_old:158,itc_value:44100,interest_liability:0,payment_status:"PAYMENT_PENDING",days_left:22,action:"Pay within 22 days to retain ITC ₹44,100"},
  {invoice_id:"pay-1218",invoice_no:"INV-1218",supplier_name:"Jain Logistics UP",supplier_gstin:"09AAACJ6543M1Z9",invoice_date:"2024-03-22",days_old:146,itc_value:28800,interest_liability:0,payment_status:"PAYMENT_PENDING",days_left:34,action:"Pay within 34 days to retain ITC ₹28,800"},
];

export const GRAPH_NODES = [
  {id:"n1",gstin:"27AABCM1234F1Z5",name:"Mahindra Castings",risk:82,type:"GSTIN",x:100,y:80},
  {id:"n2",gstin:"07AAFCS9876K1Z3",name:"Flex Systems",risk:67,type:"GSTIN",x:300,y:50},
  {id:"n3",gstin:"24AAACG8765H1Z7",name:"Gujarat Agro",risk:71,type:"GSTIN",x:500,y:80},
  {id:"n4",gstin:"33AAECS3456J1Z1",name:"Chennai Elec",risk:55,type:"GSTIN",x:600,y:200},
  {id:"n5",gstin:"09AAACJ6543M1Z9",name:"Jain Logistics",risk:78,type:"GSTIN",x:450,y:260},
  {id:"n6",gstin:"29AAACG2345N1Z2",name:"Bangalore Auto",risk:44,type:"GSTIN",x:250,y:300},
  {id:"n7",gstin:"07AAACL4567P1Z6",name:"Delhi Cloud",risk:31,type:"GSTIN",x:80,y:250},
  {id:"n8",gstin:"29AADCV5678B1ZP",name:"ACME Exports",risk:22,type:"GSTIN",x:350,y:180},
  {id:"n9",label:"INV-0042\nCRITICAL",type:"Mismatch",x:180,y:160},
  {id:"n10",label:"INV-0234\nCRITICAL",type:"Mismatch",x:420,y:140}
];

export const GRAPH_EDGES = [
  {from:"n1",to:"n2"},{from:"n2",to:"n3"},{from:"n3",to:"n1"},
  {from:"n4",to:"n5"},{from:"n5",to:"n6"},{from:"n6",to:"n8"},
  {from:"n7",to:"n8"},{from:"n1",to:"n9"},{from:"n3",to:"n10"},{from:"n2",to:"n4"}
];

export const ITC_CHAIN_HOPS = [
  {hop:0,name:"ACME Exports Ltd (Recipient)",gstin:"29AADCV5678B1ZP",itc_value:4520000,status:"SAFE",note:"Recipient — ITC claimed here",color:"#22c55e"},
  {hop:1,name:"Mahindra Castings Pvt Ltd",gstin:"27AABCM1234F1Z5",itc_value:1850000,status:"WARN",note:"2 mismatches detected. IRN risk present.",color:"#f59e0b"},
  {hop:2,name:"Gujarat Agro Chemicals",gstin:"24AAACG8765H1Z7",itc_value:980000,status:"RISKY",note:"⛔ INVOICE_MISSING_2B — ITC blocked here",color:"#ef4444"},
  {hop:3,name:"Jain Logistics UP",gstin:"09AAACJ6543M1Z9",itc_value:430000,status:"WARN",note:"Filing streak only 5 months — monitoring",color:"#f59e0b"},
  {hop:4,name:"Flex Systems India",gstin:"07AAFCS9876K1Z3",itc_value:210000,status:"SAFE",note:"No mismatches at this upstream hop",color:"#22c55e"}
];

export const PREDICTIONS = [
  {name:"Mahindra Castings",gstin:"27AABCM1234F1Z5",current:82,predicted:91,trend:"up",factors:["Critical IRN mismatch","High-risk neighbors","Streak only 2 months"]},
  {name:"Jain Logistics UP",gstin:"09AAACJ6543M1Z9",current:78,predicted:83,trend:"up",factors:["Multiple mismatches","Low filing streak (5 months)"]},
  {name:"Gujarat Agro",gstin:"24AAACG8765H1Z7",current:71,predicted:68,trend:"down",factors:["Resolved 2 mismatches","Filing improving"]},
  {name:"Flex Systems",gstin:"07AAFCS9876K1Z3",current:67,predicted:72,trend:"up",factors:["Risky trading partners","AMOUNT_MISMATCH pattern"]},
  {name:"Chennai Electrical",gstin:"33AAECS3456J1Z1",current:55,predicted:48,trend:"down",factors:["Filing streak improving","Mismatches resolved"]},
  {name:"Bangalore Auto Parts",gstin:"29AAACG2345N1Z2",current:44,predicted:41,trend:"down",factors:["Stable filing","Low mismatch rate"]},
  {name:"Delhi Cloud Tech",gstin:"07AAACL4567P1Z6",current:31,predicted:29,trend:"down",factors:["22-month streak","Clean record"]},
  {name:"ACME Exports Ltd",gstin:"29AADCV5678B1ZP",current:22,predicted:22,trend:"stable",factors:["Zero mismatches","24-month perfect streak"]}
];

export const AI_INSIGHTS = PREDICTIONS.filter(p => p.trend === 'up').slice(0, 3);

export const NODES = [
  {id:"n0", label:"ACME Exports", gstin:"29AADCV5678B1ZP", type:"GSTIN", hop:0,
   risk:22, category:"LOW", sector:"Export", state:"Karnataka", itc:4520000,
   filingStreak:24, mismatches:0, status:"SAFE"},
  {id:"n1", label:"Mahindra Castings", gstin:"27AABCM1234F1Z5", type:"GSTIN", hop:1,
   risk:82, category:"CRITICAL", sector:"Manufacturing", state:"Maharashtra", itc:1850000,
   filingStreak:2, mismatches:8, status:"WARN"},
  {id:"n2", label:"Flex Systems", gstin:"07AAFCS9876K1Z3", type:"GSTIN", hop:2,
   risk:67, category:"HIGH", sector:"Services", state:"Delhi", itc:940000,
   filingStreak:7, mismatches:5, status:"WARN"},
  {id:"n3", label:"Gujarat Agro", gstin:"24AAACG8765H1Z7", type:"GSTIN", hop:2,
   risk:71, category:"HIGH", sector:"Manufacturing", state:"Gujarat", itc:980000,
   filingStreak:4, mismatches:6, status:"BLOCKED"},
  {id:"n4", label:"Chennai Electrical", gstin:"33AAECS3456J1Z1", type:"GSTIN", hop:3,
   risk:55, category:"MEDIUM", sector:"Trading", state:"Tamil Nadu", itc:430000,
   filingStreak:11, mismatches:3, status:"WARN"},
  {id:"n5", label:"Jain Logistics", gstin:"09AAACJ6543M1Z9", type:"GSTIN", hop:3,
   risk:78, category:"HIGH", sector:"Services", state:"UP", itc:380000,
   filingStreak:5, mismatches:4, status:"WARN"},
  {id:"n6", label:"Delhi Cloud Tech", gstin:"07AAACL4567P1Z6", type:"GSTIN", hop:4,
   risk:31, category:"LOW", sector:"Services", state:"Delhi", itc:210000,
   filingStreak:22, mismatches:1, status:"SAFE"},
  {id:"n7", label:"Bangalore Auto", gstin:"29AAACG2345N1Z2", type:"GSTIN", hop:4,
   risk:44, category:"MEDIUM", sector:"Manufacturing", state:"Karnataka", itc:175000,
   filingStreak:16, mismatches:2, status:"WARN"},
  {id:"m1", label:"IRN Invalid\nINV-0042", type:"MISMATCH", itc:51300, riskLevel:"CRITICAL"},
  {id:"m2", label:"Missing 2B\nINV-0091", type:"MISMATCH", itc:17730, riskLevel:"CRITICAL"},
  {id:"m3", label:"Amt Mismatch\nINV-0078", type:"MISMATCH", itc:4320, riskLevel:"HIGH"},
  {id:"g1r1", label:"GSTR-1\nOct 2024", type:"GSTR", gstrType:"GSTR1", filed:true,  period:"102024", entity:"n1"},
  {id:"g1r2", label:"GSTR-2B\nOct 2024", type:"GSTR", gstrType:"GSTR2B", filed:true, period:"102024", entity:"n0"},
  {id:"g2r1", label:"GSTR-1\nOct 2024", type:"GSTR", gstrType:"GSTR1", filed:false, period:"102024", entity:"n3"},
  {id:"g3b",  label:"GSTR-3B\nOct 2024", type:"GSTR", gstrType:"GSTR3B", filed:true, period:"102024", entity:"n0"},
];

export const LINKS = [
  {source:"n0", target:"n1", type:"PURCHASED",    amount:1850000, label:"₹18.5L"},
  {source:"n0", target:"n2", type:"PURCHASED",    amount:940000,  label:"₹9.4L"},
  {source:"n1", target:"n3", type:"PURCHASED",    amount:980000,  label:"₹9.8L"},
  {source:"n1", target:"n4", type:"PURCHASED",    amount:430000,  label:"₹4.3L"},
  {source:"n2", target:"n5", type:"PURCHASED",    amount:380000,  label:"₹3.8L"},
  {source:"n3", target:"n6", type:"PURCHASED",    amount:210000,  label:"₹2.1L"},
  {source:"n4", target:"n7", type:"PURCHASED",    amount:175000,  label:"₹1.75L"},
  {source:"n1", target:"m1", type:"HAS_MISMATCH", amount:51300,  label:"CRITICAL"},
  {source:"n3", target:"m2", type:"HAS_MISMATCH", amount:17730,  label:"CRITICAL"},
  {source:"n2", target:"m3", type:"HAS_MISMATCH", amount:4320,   label:"HIGH"},
  {source:"n1",  target:"g1r1", type:"FILED",     amount:0, label:"Filed 11-Nov"},
  {source:"n0",  target:"g1r2", type:"REFLECTED", amount:0, label:"Auto-gen 14-Nov"},
  {source:"n3",  target:"g2r1", type:"FILED",     amount:0, label:"NOT FILED"},
  {source:"n0",  target:"g3b",  type:"FILED",     amount:0, label:"Filed 20-Nov"},
  {source:"n1", target:"n2", type:"CIRCULAR",   amount:220000, label:"₹2.2L CIRCULAR"},
  {source:"n2", target:"n3", type:"CIRCULAR",   amount:210000, label:"₹2.1L CIRCULAR"},
  {source:"n3", target:"n1", type:"CIRCULAR",   amount:215000, label:"₹2.15L CIRCULAR"},
];

export const ITC_STEPS = [
  {hopNodes:["n0"],         msg:"Starting BFS from ACME Exports (Recipient)", type:"info"},
  {hopNodes:["n1","n2"],    msg:"Hop 1 — Traversing to direct suppliers", type:"hop"},
  {hopNodes:["m1","m3"],    msg:"⚠ Mismatch events found at Mahindra Castings & Flex Systems", type:"warn"},
  {hopNodes:["n3","n4","n5"],msg:"Hop 2 — Traversing second-tier suppliers", type:"hop"},
  {hopNodes:["m2"],         msg:"🚨 CRITICAL: Gujarat Agro missing from GSTR-2B — ITC BLOCKED", type:"crit"},
  {hopNodes:["n6","n7"],    msg:"Hop 3 — Traversing third-tier suppliers", type:"hop"},
  {hopNodes:[],             msg:"BFS complete. Chain risk: HIGH. ₹9.8L blocked at Hop 2.", type:"crit"},
];

export const GSTR_STEPS = [
  {nodes:["n1"],     links:["n1-g1r1"], msg:"Supplier GSTR-1 filed by Mahindra Castings (11-Nov deadline)", type:"ok"},
  {nodes:["n0"],     links:["n0-g1r2"], msg:"GSTR-2B auto-populated for ACME Exports on 14-Nov", type:"info"},
  {nodes:["n3"],     links:["n3-g2r1"], msg:"🚨 CRITICAL: Gujarat Agro did NOT file GSTR-1 — Invoice won't appear in 2B", type:"crit"},
  {nodes:["n0"],     links:["n0-g3b"],  msg:"ACME files GSTR-3B and claims ITC — Gujarat Agro invoices INADMISSIBLE", type:"warn"},
];

export const FRAUD_STEPS = [
  {nodes:["n1"],           msg:"Starting fraud scan from Mahindra Castings", type:"info"},
  {nodes:["n1","n2"],      msg:"Checking outgoing transactions — n1 → n2 (₹2.2L)", type:"hop"},
  {nodes:["n1","n2","n3"], msg:"Following chain — n2 → n3 (₹2.1L)", type:"hop"},
  {nodes:["n1","n2","n3"], msg:"🚨 CYCLE DETECTED: n3 → n1 — Circular Trading Ring!", type:"crit"},
  {nodes:["n1","n2","n3"], msg:"Ring value: ₹6.45L | Generates fake ITC | Section 132 CGST Act", type:"crit"},
];
