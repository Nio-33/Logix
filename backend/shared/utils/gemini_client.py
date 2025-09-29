"""
Google Gemini AI Client for Logix Platform
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for Google Gemini AI API"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not provided - AI features will be disabled")
            self.enabled = False
            return
        
        self.enabled = True
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize models
        self.chat_model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        
        # Safety settings
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        logger.info("Gemini AI client initialized successfully")
    
    def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate text using Gemini Pro
        """
        if not getattr(self, 'enabled', True):
            return "AI features are disabled in development mode"
        
        try:
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": max_tokens,
            }
            
            response = self.chat_model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {e}")
            raise
    
    def optimize_route(self, stops: List[Dict[str, Any]], constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Optimize delivery route using Gemini AI
        """
        try:
            # Prepare route optimization prompt
            prompt = self._build_route_optimization_prompt(stops, constraints)
            
            response = self.generate_text(prompt, max_tokens=2000)
            
            # Parse the response to extract route optimization
            optimized_route = self._parse_route_response(response, stops)
            
            return optimized_route
            
        except Exception as e:
            logger.error(f"Error optimizing route: {e}")
            raise
    
    def chatbot_response(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """
        Generate chatbot response for customer support
        """
        try:
            # Build chatbot prompt with context
            prompt = self._build_chatbot_prompt(user_message, context)
            
            response = self.generate_text(prompt, max_tokens=500)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating chatbot response: {e}")
            return "I'm sorry, I'm having trouble processing your request right now. Please try again or contact our support team."
    
    def analyze_delivery_image(self, image_data: bytes, context: str = "") -> Dict[str, Any]:
        """
        Analyze delivery proof images using Gemini Vision
        """
        try:
            # Prepare the prompt for image analysis
            prompt = f"""
            Analyze this delivery proof image and provide the following information:
            1. Type of delivery (package, envelope, etc.)
            2. Condition assessment (good, damaged, etc.)
            3. Location type (residential, commercial, etc.)
            4. Any visible issues or concerns
            5. Confidence level in the delivery proof
            
            Context: {context}
            
            Provide response in JSON format.
            """
            
            # Convert image data to the required format
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_data
            }
            
            response = self.vision_model.generate_content(
                [prompt, image_part],
                safety_settings=self.safety_settings
            )
            
            # Parse response
            try:
                analysis = json.loads(response.text)
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured response
                analysis = {
                    "analysis": response.text,
                    "type": "unknown",
                    "condition": "unknown",
                    "location_type": "unknown",
                    "issues": [],
                    "confidence": 0.5
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing delivery image: {e}")
            raise
    
    def predict_demand(self, historical_data: List[Dict[str, Any]], 
                      product_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Predict demand for inventory planning
        """
        try:
            prompt = self._build_demand_prediction_prompt(historical_data, product_info)
            
            response = self.generate_text(prompt, max_tokens=1000)
            
            # Parse prediction response
            prediction = self._parse_demand_prediction(response)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting demand: {e}")
            raise
    
    def generate_delivery_summary(self, delivery_data: List[Dict[str, Any]]) -> str:
        """
        Generate AI-powered delivery performance summary
        """
        try:
            prompt = f"""
            Analyze the following delivery performance data and provide a comprehensive summary:
            
            Delivery Data:
            {json.dumps(delivery_data, indent=2)}
            
            Please provide:
            1. Overall performance assessment
            2. Key metrics and trends
            3. Areas for improvement
            4. Recommendations for optimization
            5. Notable achievements or concerns
            
            Format the response as a professional executive summary.
            """
            
            summary = self.generate_text(prompt, max_tokens=1500)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating delivery summary: {e}")
            raise
    
    def _build_route_optimization_prompt(self, stops: List[Dict[str, Any]], 
                                       constraints: Dict[str, Any] = None) -> str:
        """
        Build prompt for route optimization
        """
        prompt = f"""
        You are an expert logistics route optimizer. Optimize the following delivery route:
        
        Delivery Stops:
        {json.dumps(stops, indent=2)}
        
        Constraints:
        {json.dumps(constraints or {}, indent=2)}
        
        Consider the following factors:
        1. Distance and travel time between stops
        2. Time windows for deliveries
        3. Vehicle capacity and restrictions
        4. Traffic patterns and road conditions
        5. Driver break requirements
        6. Fuel efficiency
        
        Provide the optimized route with:
        1. Optimal stop sequence
        2. Estimated total distance and time
        3. Fuel consumption estimate
        4. Recommendations for timing
        5. Alternative routes if applicable
        
        Format response as JSON with the structure:
        {{
            "optimized_sequence": [stop_ids],
            "total_distance_km": number,
            "total_time_minutes": number,
            "fuel_estimate_liters": number,
            "recommendations": ["recommendation1", "recommendation2"],
            "alternative_routes": []
        }}
        """
        
        return prompt
    
    def _build_chatbot_prompt(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """
        Build prompt for chatbot response
        """
        context_str = ""
        if context:
            context_str = f"""
            Context Information:
            - Customer ID: {context.get('customer_id', 'Unknown')}
            - Order ID: {context.get('order_id', 'None')}
            - Previous orders: {context.get('order_history', [])}
            - Account status: {context.get('account_status', 'Active')}
            """
        
        prompt = f"""
        You are a helpful customer service assistant for Logix, an AI-powered logistics platform.
        
        {context_str}
        
        Customer Message: "{user_message}"
        
        Guidelines:
        1. Be friendly, professional, and helpful
        2. Provide accurate information about orders, deliveries, and services
        3. If you need more information, ask clarifying questions
        4. For complex issues, suggest contacting human support
        5. Always maintain customer privacy and security
        6. Keep responses concise but informative
        
        Respond naturally and helpfully to the customer's inquiry.
        """
        
        return prompt
    
    def _build_demand_prediction_prompt(self, historical_data: List[Dict[str, Any]], 
                                      product_info: Dict[str, Any] = None) -> str:
        """
        Build prompt for demand prediction
        """
        prompt = f"""
        You are an expert demand forecasting analyst. Analyze the following historical sales data 
        and predict future demand:
        
        Historical Data:
        {json.dumps(historical_data, indent=2)}
        
        Product Information:
        {json.dumps(product_info or {}, indent=2)}
        
        Consider these factors:
        1. Seasonal trends and patterns
        2. Growth trajectories
        3. Market conditions
        4. Product lifecycle stage
        5. External factors (holidays, events, etc.)
        
        Provide predictions for:
        1. Next 30 days demand
        2. Next 90 days demand
        3. Confidence intervals
        4. Key assumptions
        5. Risk factors
        
        Format as JSON:
        {{
            "predictions": {{
                "30_days": {{"demand": number, "confidence": number}},
                "90_days": {{"demand": number, "confidence": number}}
            }},
            "trends": ["trend1", "trend2"],
            "assumptions": ["assumption1", "assumption2"],
            "risks": ["risk1", "risk2"]
        }}
        """
        
        return prompt
    
    def _parse_route_response(self, response: str, original_stops: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse route optimization response
        """
        try:
            # Try to parse as JSON first
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic response
            logger.warning("Failed to parse route optimization response as JSON")
            return {
                "optimized_sequence": [stop.get('id', i) for i, stop in enumerate(original_stops)],
                "total_distance_km": 0,
                "total_time_minutes": 0,
                "fuel_estimate_liters": 0,
                "recommendations": ["Unable to parse optimization results"],
                "alternative_routes": [],
                "raw_response": response
            }
    
    def _parse_demand_prediction(self, response: str) -> Dict[str, Any]:
        """
        Parse demand prediction response
        """
        try:
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            logger.warning("Failed to parse demand prediction response as JSON")
            return {
                "predictions": {
                    "30_days": {"demand": 0, "confidence": 0.5},
                    "90_days": {"demand": 0, "confidence": 0.5}
                },
                "trends": [],
                "assumptions": [],
                "risks": [],
                "raw_response": response
            }