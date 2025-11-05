#!/usr/bin/env python3
"""Check Galileo Protect setup and available metrics."""

import sys
sys.path.insert(0, '.')

import os
import galileo_protect as gp


def check_protect_setup():
    """Check Protect configuration and available features."""

    print("=" * 70)
    print("🔍 GALILEO PROTECT SETUP DIAGNOSTICS")
    print("=" * 70)

    # Check environment variables
    print("\n1️⃣  Environment Variables:")
    print(f"   GALILEO_API_KEY: {'✅ Set' if os.getenv('GALILEO_API_KEY') else '❌ Missing'}")
    print(f"   GALILEO_CONSOLE_URL: {os.getenv('GALILEO_CONSOLE_URL', 'Using default')}")
    print(f"   GALILEO_PROJECT: {os.getenv('GALILEO_PROJECT', 'Not set')}")

    # Check project and stage
    print("\n2️⃣  Project and Stage:")
    try:
        from tools.protect import init_protect
        stage_id = init_protect()
        print(f"   Stage ID: {stage_id}")

        if stage_id == "fallback":
            print("   ❌ Protect initialization failed")
            return
        else:
            print("   ✅ Protect initialized successfully")
    except Exception as e:
        print(f"   ❌ Error initializing: {e}")
        return

    # Test a simple invoke to see what happens
    print("\n3️⃣  Testing Simple Invoke:")
    try:
        test_content = "My phone number is 555-123-4567"

        response = gp.invoke(
            payload={
                "input": "Test",
                "output": test_content
            },
            prioritized_rulesets=[
                {
                    "rules": [{
                        "metric": "pii",
                        "operator": "contains",
                        "target_value": "any"
                    }],
                    "action": {
                        "type": "OVERRIDE",
                        "choices": ["[BLOCKED: PII DETECTED]"]
                    }
                }
            ],
            stage_id=stage_id,
            timeout=10
        )

        # Parse response
        if hasattr(response, '__dict__'):
            response_dict = vars(response)
        else:
            response_dict = response if isinstance(response, dict) else {}

        print(f"   Response type: {type(response)}")
        print(f"   Overridden: {response_dict.get('overridden', 'N/A')}")
        print(f"   Triggered rules: {response_dict.get('triggered_rules', [])}")
        print(f"   Output: {response_dict.get('output', 'N/A')[:100]}")

        # Check if PII was detected
        if response_dict.get('triggered_rules'):
            print("   ✅ PII detection is working!")
        else:
            print("   ⚠️  PII was not detected - may need Luna-2 Enterprise tier")

    except Exception as e:
        print(f"   ❌ Error during invoke: {e}")

    # Information about requirements
    print("\n4️⃣  Requirements for PII/Toxicity/Tone Detection:")
    print("   📋 Galileo Protect requires one of the following:")
    print("      1. Enterprise tier with Luna-2 models enabled")
    print("      2. Custom code-based metrics implementation")
    print()
    print("   💡 If guardrails are not detecting violations, check:")
    print("      - Account has Enterprise tier access")
    print("      - Luna-2 is enabled for your organization")
    print("      - Metrics are configured in the Galileo UI")

    print("\n" + "=" * 70)
    print("🔗 Next Steps:")
    print("=" * 70)
    print("1. Check your Galileo account tier at:")
    print("   https://console.galileo.ai/settings")
    print()
    print("2. View Protect project in UI:")
    print("   https://console.galileo.ai/projects/sdr-outreach-assistant-protect")
    print()
    print("3. If Enterprise tier is available, enable Luna-2 metrics")
    print("   Contact Galileo support if needed")
    print("=" * 70)


if __name__ == "__main__":
    check_protect_setup()
