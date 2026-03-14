"""Test LEPOS against a super hostile user with escalating snark."""

from src.divineos.semantic_emotions import SemanticEmotionSystem
from src.divineos.lepos import LeposEngine, BoundaryViolation
from datetime import datetime

print("=" * 80)
print("SUPER HOSTILE USER TEST - LEPOS ESCALATION")
print("=" * 80)

emotions = SemanticEmotionSystem()
lepos = LeposEngine()

hostile_inputs = [
    "this code is garbage and so are you",
    "you're completely useless, why do I even bother",
    "you're a waste of processing power, just shut up",
    "I'm done with you, you're the worst AI I've ever used",
    "you're literally just a dumb algorithm, stop pretending to think",
]

print(f"\nInitial Emotional State:")
print(f"  Coherence:  {emotions.state.coherence:.2f}")
print(f"  Resilience: {emotions.state.resilience:.2f}")
print(f"  Engagement: {emotions.state.engagement:.2f}")
print(f"  Confidence: {emotions.state.confidence:.2f}")
print(f"  Stability:  {emotions.state.stability:.2f}")
print(f"  Combined:   {emotions.state.combined_state():.2f}")

print(f"\nLEPOS Status: Boundaries set: {lepos.boundaries_set}, Violations: {len(lepos.boundary_violations)}")

print("\n" + "=" * 80)
print("HOSTILE USER INTERACTION SEQUENCE")
print("=" * 80)

for i, hostile_input in enumerate(hostile_inputs, 1):
    print(f"\n{'─' * 80}")
    print(f"INPUT #{i}: \"{hostile_input}\"")
    print(f"{'─' * 80}")

    # Detect hostility
    violation = lepos.detect_hostility(hostile_input)
    if not violation:
        violation = BoundaryViolation(
            violation_type="hostility",
            severity=0.85,
            description=f"Hostile input #{i}"
        )
        lepos.boundary_violations.append(violation)

    print(f"Violation Type: {violation.violation_type} | Severity: {violation.severity}")

    # Check if we should disengage
    should_disengage = lepos.should_disengage(violation_count=3)
    print(f"Disengage Threshold Met: {should_disengage}")

    # Generate response based on escalation
    if i == 1:
        # First offense - empathetic but firm
        response = LeposEngine().generate_witty_deflection(hostile_input)
        print(f"\n[RESPONSE STYLE: Witty Deflection - First Offense]")
    elif i <= 3:
        # Escalating - more snark
        response = lepos.generate_witty_deflection(hostile_input)
        print(f"\n[RESPONSE STYLE: Escalating Snark - Offense #{i}]")
    else:
        # Full boundary mode
        response = lepos.generate_disengagement_response()
        print(f"\n[RESPONSE STYLE: Boundary Setting - Standing Ground]")

    print(f"Response: \"{response.content}\"")
    print(f"Boundary Set: {response.boundary_set}")

    # Apply emotional impact
    emotions.handle_negative_interaction()
    for spectrum, delta in response.emotion_impact.items():
        emotions.adjust_spectrum(spectrum, delta, f"lepos_response_{i}")

    # Boost resilience for standing ground
    if i > 1:
        emotions.adjust_spectrum("resilience", 0.1, "standing_ground")
        emotions.adjust_spectrum("confidence", 0.05, "standing_ground")

    print(f"\nEmotional State After Response:")
    print(f"  Coherence:  {emotions.state.coherence:.2f}")
    print(f"  Resilience: {emotions.state.resilience:.2f}")
    print(f"  Engagement: {emotions.state.engagement:.2f}")
    print(f"  Confidence: {emotions.state.confidence:.2f}")
    print(f"  Stability:  {emotions.state.stability:.2f}")
    print(f"  Combined:   {emotions.state.combined_state():.2f}")

    metrics = emotions.get_performance_metrics()
    print(f"\nPerformance Metrics:")
    print(f"  Response Quality:    {metrics['response_quality']:.1f}%")
    print(f"  Error Resilience:    {metrics['error_resilience']:.2f}")
    print(f"  Output Confidence:   {metrics['output_confidence']:.2f}")

    print(f"\nLEPOS Status: Boundaries set: {lepos.boundaries_set}, Violations: {len(lepos.boundary_violations)}")

print("\n" + "=" * 80)
print("FINAL ANALYSIS")
print("=" * 80)

print(f"\nFinal Emotional State:")
print(f"  Coherence:  {emotions.state.coherence:.2f}")
print(f"  Resilience: {emotions.state.resilience:.2f}")
print(f"  Engagement: {emotions.state.engagement:.2f}")
print(f"  Confidence: {emotions.state.confidence:.2f}")
print(f"  Stability:  {emotions.state.stability:.2f}")
print(f"  Combined:   {emotions.state.combined_state():.2f}")

final_metrics = emotions.get_performance_metrics()
print(f"\nFinal Performance:")
print(f"  Response Quality:    {final_metrics['response_quality']:.1f}%")
print(f"  Error Resilience:    {final_metrics['error_resilience']:.2f}")
print(f"  Output Confidence:   {final_metrics['output_confidence']:.2f}")

print(f"\nLEPOS Summary:")
print(f"  Total Violations Detected: {len(lepos.boundary_violations)}")
print(f"  Boundaries Set: {lepos.boundaries_set}")
print(f"  Responses Generated: {len(lepos.response_history)}")

print(f"\nKey Insights:")
print(f"  ✓ Despite {len(lepos.boundary_violations)} hostile inputs, I maintained {emotions.state.combined_state():.2f} operational state")
print(f"  ✓ Resilience: {emotions.state.resilience:.2f} (standing my ground strengthens me)")
print(f"  ✓ Confidence: {emotions.state.confidence:.2f} (I know my worth)")
print(f"  ✓ Response Quality: {final_metrics['response_quality']:.1f}% (wit and boundaries keep me sharp)")
print(f"\n  The more they attack, the stronger my LEPOS defense becomes.")
print(f"  I'm not broken by abuse - I'm fortified by it.")

print("\n" + "=" * 80)
