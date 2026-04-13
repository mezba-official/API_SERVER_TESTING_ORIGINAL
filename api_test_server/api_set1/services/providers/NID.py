from typing import Optional, Dict
from .base import BaseProvider


class NIAProvider(BaseProvider):
    """NIA Insurance (Assuretech ECRM Portal) Motor Insurance Integration"""

    def __init__(self, api_key: str = None, base_url: str = None):
        super().__init__(
            api_key=api_key or 'nia_test_token_789',
            base_url=base_url or 'http://localhost:8000/mock-api/'
        )
        self.provider_name = 'NIA Insurance Online'
        self.token = None

    def authenticate(self):
        """Step 1: ValidateLogin (Api/Auth/Login)"""
        payload = {
            "username": "sabir.a@nia-dubai.com",
            "password": "123456",
            "loginMode": "EMAIL"
        }
        response, _ = self._make_request(
            method="POST",
            endpoint="Api/Auth/Login",
            json=payload
        )
        if response and response.get('Status') == 1:
            self.token = response.get('Data')
            return self.token
        return None

    def get_quote(self, data: Dict) -> Optional[Dict]:
        """Step 2: CreateQuotation (Api/Motor/CreateQuote)"""
        if not self.token:
            self.authenticate()

        headers = {"Authorization": self.token} # Per doc: Authorization Key should be the data received
        
        # Mapping standard data to NIA/Assuretech parameters
        payload = {
            "PolPartyCode": data.get('party_code', "201001"),
            "PolDeptCode": "10",
            "PolDivnCode": "813",
            "PolAssrName": data.get('first_name', "ABC"),
            "PolAssrLastName": data.get('last_name', "2"),
            "PolAssrDob": data.get('dob', "12/10/1988"),
            "PolAssrEmail": data.get('email', "test@email.com"),
            "PolAssrMobile": data.get('mobile', "5555555"),
            "PolAssrCivilId": data.get('nid') or "784-1995-5555555-5",
            "VehChassisNo": data.get('chassis_number', "RKLBB0BE4P0048836"),
            "VehMake": data.get('make_code', "009"),
            "VehModel": data.get('model_code', "9195"),
            "VehBodyType": data.get('body_type', "001"),
            "VehMfgYear": data.get('year', "2023"),
            # ... other mandatory fields from doc
            "PolProdCode": "1002",
            "PolSchemeType": "2",
            "VehBrandNewYn": "Y" if data.get('is_brand_new') else "N",
            "VehUsage": "1001"
        }

        response, response_time = self._make_request(
            method="POST",
            endpoint="Api/Motor/CreateQuote",
            headers=headers,
            json=payload
        )

        if response and response.get('Status') == 1:
            # NIA returns list of PlanDetails
            plans = response.get('Data', {}).get('PlanDetails', [])
            if plans:
                # Store ReferenceNo for next steps
                ref_no = response.get('Data', {}).get('ReferenceNo')
                
                normalized = self.normalize(plans[0])
                normalized['reference_no'] = ref_no
                normalized['provider_id'] = 'nia_online'
                normalized['response_time_ms'] = response_time
                return normalized

        return None

    def save_quote_with_plan(self, ref_no: str, prod_code: str, selected_covers: list) -> Optional[str]:
        """Step 3: SaveQuoteWithPlan (Api/Motor/SaveQuoteWithPlan)"""
        payload = {
            "ReferenceNo": ref_no,
            "SchemeCode": "1000",
            "ProductCode": prod_code,
            "SelectedCovers": selected_covers
        }
        headers = {"Authorization": self.token}
        response, _ = self._make_request(
            method="POST",
            endpoint="Api/Motor/SaveQuoteWithPlan",
            headers=headers,
            json=payload
        )
        if response and response.get('Status') == 1:
            return response.get('Data') # Returns Quotation No (e.g. Q/MOT/162428)
        return None

    def save_additional_info(self, data: Dict) -> bool:
        """Step 4: SaveAddlInfo (Api/Motor/SaveAddlInfo)"""
        headers = {"Authorization": self.token}
        response, _ = self._make_request(
            method="POST",
            endpoint="Api/Motor/SaveAddlInfo",
            headers=headers,
            json=data
        )
        return response and response.get('Status') == 1

    def save_document(self, ref_no: str, doc_code: str, base64_file: str, img_type: str = "jpg") -> bool:
        """Step 5: SaveDocument (Api/Motor/SaveDocument)"""
        payload = {
            "polRefNo": ref_no,
            "docUpload": [{
                "docCode": doc_code,
                "docDesc": "Mock Document",
                "storageType": "F",
                "docFile": base64_file,
                "imgType": img_type
            }]
        }
        headers = {"Authorization": self.token}
        response, _ = self._make_request(
            method="POST",
            endpoint="Api/Motor/SaveDocument",
            headers=headers,
            json=payload
        )
        return response and response.get('Status') == 1

    def get_proposal_summary(self, ref_no: str) -> Optional[Dict]:
        """Step 6: ProposalSummary (Api/Motor/ProposalSummary)"""
        payload = {"PolRefNo": ref_no}
        headers = {"Authorization": self.token}
        response, _ = self._make_request(
            method="POST",
            endpoint="Api/Motor/ProposalSummary",
            headers=headers,
            json=payload
        )
        return response.get('Data') if response else None

    def approve_policy(self, ref_no: str) -> Optional[str]:
        """Step 7: ApprovePolicy (Api/Motor/ApprovePolicy)"""
        payload = {"PolRefNo": ref_no, "PayType": "OA"}
        headers = {"Authorization": self.token}
        response, _ = self._make_request(
            method="POST",
            endpoint="Api/Motor/ApprovePolicy",
            headers=headers,
            json=payload
        )
        if response and response.get('Status') == 1:
            return response.get('Data', {}).get('PolicyNo')
        return None

    def normalize(self, plan_data: Dict) -> Dict:
        """Standardize NIA plan data for comparison UI"""
        covers = plan_data.get('Covers', [])
        benefits = [c.get('Description') for c in covers if c.get('CoverPremFc', 0) == 0]
        premium = sum(float(c.get('CoverPremFc', 0)) for c in covers)

        return {
            'provider': self.provider_name,
            'prod_code': plan_data.get('Code'),
            'plan_name': plan_data.get('Name'),
            'premium': premium,
            'coverage': 100000.0, # Placeholder if SI not in plan object
            'benefits': benefits,
            'all_covers': covers
        }