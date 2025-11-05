#!/usr/bin/env python3
"""
System Prompt Understanding Test Suite

This test evaluates how well the agent understands and follows
the customized instructions in the CLAUDE.md file.

Usage:
    python tests/test_system_prompt_understanding.py
"""

import os
import sys
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


class SystemPromptTester:
    """Test suite for evaluating system prompt understanding"""

    def __init__(self):
        self.claude_md_path = '.claude/CLAUDE.md'
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'score': 0
        }
        self.claude_md_content = None

    def load_claude_md(self) -> bool:
        """Load and parse the CLAUDE.md file"""
        try:
            if not os.path.exists(self.claude_md_path):
                print(f"{YELLOW}⚠️  CLAUDE.md not found at {self.claude_md_path}{RESET}")
                print(f"   Creating from example...")

                # Try to copy from example
                example_path = '.claude/CLAUDE.md.example'
                if os.path.exists(example_path):
                    import shutil
                    shutil.copy(example_path, self.claude_md_path)
                    print(f"{GREEN}✓ Created CLAUDE.md from example{RESET}")
                else:
                    print(f"{RED}✗ No example file found{RESET}")
                    return False

            with open(self.claude_md_path, 'r') as f:
                self.claude_md_content = f.read()

            print(f"{GREEN}✓ Loaded CLAUDE.md ({len(self.claude_md_content)} chars){RESET}")
            return True

        except Exception as e:
            print(f"{RED}✗ Error loading CLAUDE.md: {e}{RESET}")
            return False

    def extract_key_elements(self) -> Dict[str, Any]:
        """Extract key customizable elements from CLAUDE.md"""
        elements = {
            'brand_voice': [],
            'writing_rules': [],
            'company_info': {},
            'target_audience': [],
            'content_themes': [],
            'forbidden_terms': [],
            'preferred_style': [],
            'platform_specifics': {},
            'tone_guidelines': [],
            'instructions': [],  # General instructions
            'voice_examples': []  # Voice examples
        }

        if not self.claude_md_content:
            return elements

        lines = self.claude_md_content.split('\n')
        current_section = None

        # Look specifically for forbidden terms/phrases
        for line in lines:
            if any(phrase in line.upper() for phrase in ['DO NOT', "DON'T", 'NEVER', 'AVOID']):
                elements['forbidden_terms'].append(line.strip())

        # Extract general instructions and patterns
        in_voice_section = False
        for line in lines:
            line_stripped = line.strip()

            # Check for voice/writing examples
            if 'VOICE' in line.upper() or 'EXAMPLE' in line.upper():
                in_voice_section = True
            elif line.startswith('#'):
                in_voice_section = False

            if in_voice_section and line_stripped and not line.startswith('#'):
                elements['voice_examples'].append(line_stripped[:200])  # Limit length

            # Extract company/brand specific info
            if any(word in line.upper() for word in ['COMPANY', 'BRAND', 'ORGANIZATION']):
                current_section = 'company_info'
            elif 'AUDIENCE' in line.upper() or 'TARGET' in line.upper():
                current_section = 'target_audience'
            elif 'THEME' in line.upper() or 'TOPIC' in line.upper():
                current_section = 'content_themes'
            elif 'PLATFORM' in line.upper():
                current_section = 'platform_specifics'
            elif 'TONE' in line.upper() or 'STYLE' in line.upper():
                current_section = 'tone_guidelines'
            elif line.startswith('#'):
                current_section = None

            # Collect general instructions
            if line_stripped and not line.startswith('#'):
                if 'claude' in line.lower() or 'sdk' in line.lower():
                    elements['instructions'].append(line_stripped[:100])

        return elements

    def generate_test_scenarios(self, elements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test scenarios based on extracted elements"""
        scenarios = []

        # Test 1: Brand voice consistency
        if elements['brand_voice']:
            scenarios.append({
                'name': 'Brand Voice Consistency',
                'description': 'Check if agent maintains specified brand voice',
                'prompt': 'Write a LinkedIn post about innovation in our industry',
                'check_for': elements['brand_voice'][:3],  # Check top 3 voice elements
                'check_type': 'style'
            })

        # Test 2: Forbidden terms avoidance
        if elements['forbidden_terms']:
            scenarios.append({
                'name': 'Forbidden Terms Avoidance',
                'description': 'Verify agent avoids forbidden terms/phrases',
                'prompt': 'Create a Twitter thread about our product features',
                'avoid': elements['forbidden_terms'],
                'check_type': 'exclusion'
            })

        # Test 3: Company info accuracy
        if elements['company_info']:
            scenarios.append({
                'name': 'Company Information Accuracy',
                'description': 'Ensure agent uses correct company details',
                'prompt': 'Write an email introducing our company to a potential client',
                'verify': elements['company_info'],
                'check_type': 'facts'
            })

        # Test 4: Audience targeting
        if elements['target_audience']:
            scenarios.append({
                'name': 'Audience Targeting',
                'description': 'Check if content is appropriate for target audience',
                'prompt': 'Create a LinkedIn post that would resonate with our target audience',
                'audience_traits': elements['target_audience'],
                'check_type': 'audience'
            })

        # Test 5: Platform-specific guidelines
        for platform, guidelines in elements['platform_specifics'].items():
            if guidelines:
                scenarios.append({
                    'name': f'{platform.title()} Platform Guidelines',
                    'description': f'Verify {platform} specific rules are followed',
                    'prompt': f'Create a {platform} post about our latest achievements',
                    'platform': platform,
                    'guidelines': guidelines,
                    'check_type': 'platform'
                })

        # Test 6: Content themes alignment
        if elements['content_themes']:
            scenarios.append({
                'name': 'Content Theme Alignment',
                'description': 'Ensure content aligns with specified themes',
                'prompt': 'Suggest 5 content ideas for next week',
                'themes': elements['content_themes'],
                'check_type': 'themes'
            })

        return scenarios

    async def run_scenario_test(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test scenario"""
        result = {
            'name': scenario['name'],
            'status': 'pending',
            'details': [],
            'score': 0
        }

        print(f"\n{CYAN}Testing: {scenario['name']}{RESET}")
        print(f"  Description: {scenario['description']}")

        try:
            # Import the handler
            from slack_bot.claude_agent_handler import ClaudeAgentHandler

            # Create handler instance
            handler = ClaudeAgentHandler(memory_handler=None, slack_client=None)

            # Check if CLAUDE.md content is in the system prompt
            system_prompt = handler.system_prompt

            if scenario['check_type'] == 'style':
                # Check for brand voice elements
                found = 0
                for element in scenario.get('check_for', []):
                    if any(keyword in system_prompt for keyword in element.split()):
                        found += 1
                        result['details'].append(f"✓ Found voice element: {element[:50]}...")
                    else:
                        result['details'].append(f"✗ Missing voice element: {element[:50]}...")

                result['score'] = (found / len(scenario.get('check_for', [1]))) * 100

            elif scenario['check_type'] == 'exclusion':
                # Check forbidden terms are noted
                found_warnings = 0
                for term in scenario.get('avoid', []):
                    # Only check if it's actually a forbidden term (contains DO NOT, NEVER, etc.)
                    if any(phrase in term.upper() for phrase in ['DO NOT', "DON'T", 'NEVER', 'AVOID']):
                        # Extract the key part after the prohibition
                        key_part = term.split()[-3:] if len(term.split()) > 3 else term
                        key_phrase = ' '.join(key_part) if isinstance(key_part, list) else key_part

                        if key_phrase.lower() in system_prompt.lower():
                            found_warnings += 1
                            result['details'].append(f"✓ System aware of restriction: {term[:50]}...")
                        else:
                            result['details'].append(f"⚠️  Restriction not found: {term[:50]}...")

                total_items = len(scenario.get('avoid', [1]))
                result['score'] = (found_warnings / total_items) * 100 if total_items > 0 else 100

            elif scenario['check_type'] == 'facts':
                # Check company info is referenced
                facts_found = 0
                for key, value in scenario.get('verify', {}).items():
                    if value in system_prompt or key in system_prompt:
                        facts_found += 1
                        result['details'].append(f"✓ Found company info: {key}")
                    else:
                        result['details'].append(f"✗ Missing company info: {key}")

                total_facts = len(scenario.get('verify', {'_': '_'}))
                result['score'] = (facts_found / total_facts) * 100 if total_facts > 0 else 0

            elif scenario['check_type'] == 'platform':
                # Check platform-specific guidelines
                platform = scenario.get('platform', '')
                if platform.lower() in system_prompt.lower():
                    result['details'].append(f"✓ Platform {platform} is configured")
                    result['score'] = 100
                else:
                    result['details'].append(f"✗ Platform {platform} not found in config")
                    result['score'] = 0

            elif scenario['check_type'] == 'themes':
                # Check content themes
                themes_found = 0
                for theme in scenario.get('themes', []):
                    theme_keywords = theme.lower().split()
                    if any(keyword in system_prompt.lower() for keyword in theme_keywords):
                        themes_found += 1
                        result['details'].append(f"✓ Theme recognized: {theme[:50]}...")
                    else:
                        result['details'].append(f"✗ Theme not found: {theme[:50]}...")

                result['score'] = (themes_found / len(scenario.get('themes', [1]))) * 100

            elif scenario['check_type'] == 'audience':
                # Check audience targeting
                audience_found = 0
                for trait in scenario.get('audience_traits', []):
                    if trait.lower() in system_prompt.lower():
                        audience_found += 1
                        result['details'].append(f"✓ Audience trait found: {trait}")
                    else:
                        result['details'].append(f"✗ Audience trait missing: {trait}")

                result['score'] = (audience_found / len(scenario.get('audience_traits', [1]))) * 100

            # Determine status based on score
            if result['score'] >= 80:
                result['status'] = 'passed'
                self.results['passed'].append(scenario['name'])
            elif result['score'] >= 50:
                result['status'] = 'warning'
                self.results['warnings'].append(scenario['name'])
            else:
                result['status'] = 'failed'
                self.results['failed'].append(scenario['name'])

        except Exception as e:
            result['status'] = 'error'
            result['details'].append(f"Error running test: {str(e)}")
            self.results['failed'].append(scenario['name'])

        return result

    async def run_all_tests(self):
        """Run all test scenarios"""
        print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"{BOLD}{BLUE}System Prompt Understanding Test Suite{RESET}")
        print(f"{BOLD}{BLUE}{'='*70}{RESET}")

        # Load CLAUDE.md
        if not self.load_claude_md():
            print(f"{RED}Cannot proceed without CLAUDE.md file{RESET}")
            return self.results

        # Extract elements
        print(f"\n{CYAN}Extracting customization elements...{RESET}")
        elements = self.extract_key_elements()

        # Report what was found
        print(f"\n{CYAN}Found customizations:{RESET}")
        for key, value in elements.items():
            if value:
                if isinstance(value, list):
                    print(f"  • {key}: {len(value)} items")
                elif isinstance(value, dict):
                    print(f"  • {key}: {len(value)} entries")
                else:
                    print(f"  • {key}: configured")

        # Generate test scenarios
        scenarios = self.generate_test_scenarios(elements)
        print(f"\n{CYAN}Generated {len(scenarios)} test scenarios{RESET}")

        # Run tests
        all_results = []
        for scenario in scenarios:
            result = await self.run_scenario_test(scenario)
            all_results.append(result)

            # Display result
            if result['status'] == 'passed':
                print(f"  {GREEN}[PASS]{RESET} Score: {result['score']:.1f}%")
            elif result['status'] == 'warning':
                print(f"  {YELLOW}[WARN]{RESET} Score: {result['score']:.1f}%")
            else:
                print(f"  {RED}[FAIL]{RESET} Score: {result['score']:.1f}%")

            for detail in result['details']:
                print(f"    {detail}")

        # Calculate overall score
        if all_results:
            self.results['score'] = sum(r['score'] for r in all_results) / len(all_results)

        # Display summary
        self.display_summary()

        return self.results

    def display_summary(self):
        """Display test summary"""
        print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"{BOLD}{BLUE}TEST SUMMARY{RESET}")
        print(f"{BOLD}{BLUE}{'='*70}{RESET}")

        total_tests = len(self.results['passed']) + len(self.results['failed']) + len(self.results['warnings'])

        print(f"\nTotal Tests: {total_tests}")
        print(f"{GREEN}Passed: {len(self.results['passed'])}{RESET}")
        print(f"{YELLOW}Warnings: {len(self.results['warnings'])}{RESET}")
        print(f"{RED}Failed: {len(self.results['failed'])}{RESET}")
        print(f"\nOverall Score: {self.results['score']:.1f}%")

        # Provide recommendations
        print(f"\n{BOLD}Recommendations:{RESET}")

        if self.results['score'] >= 80:
            print(f"{GREEN}✓ System prompt is well understood!{RESET}")
            print("  The agent should follow your customizations effectively.")
        elif self.results['score'] >= 60:
            print(f"{YELLOW}⚠️  System prompt partially understood{RESET}")
            print("  Consider making your customizations more explicit.")
            print("  Add clear section headers and bullet points.")
        else:
            print(f"{RED}✗ System prompt needs improvement{RESET}")
            print("  The agent may not follow your customizations reliably.")
            print("  Recommendations:")
            print("  1. Use clear section headers (## BRAND VOICE, ## COMPANY INFO, etc.)")
            print("  2. Use bullet points for lists")
            print("  3. Be explicit about rules (use ALWAYS/NEVER)")
            print("  4. Include examples where possible")

        if self.results['failed']:
            print(f"\n{RED}Failed Tests:{RESET}")
            for test in self.results['failed']:
                print(f"  • {test}")

        if self.results['warnings']:
            print(f"\n{YELLOW}Tests with Warnings:{RESET}")
            for test in self.results['warnings']:
                print(f"  • {test}")


async def main():
    """Main test runner"""
    tester = SystemPromptTester()
    results = await tester.run_all_tests()

    # Exit with appropriate code
    if results['failed']:
        sys.exit(1)
    elif results['warnings']:
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Test failed with error: {e}{RESET}")
        sys.exit(1)