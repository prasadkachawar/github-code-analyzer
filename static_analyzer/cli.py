"""Command-line interface for the static analyzer."""

import sys
import os
import click
from pathlib import Path
from typing import Optional, List
from . import StaticAnalyzer, create_analyzer_from_config_file, create_default_analyzer
from .config import AnalyzerConfig, DeviationManager, create_default_config_file
from .models import Standard


@click.group()
@click.version_option(version="1.0.0")
def cli() -> None:
    """Static Code Analysis Framework for Embedded C/C++."""
    pass


@cli.command()
@click.option("--path", "-p", required=True, 
              help="Path to source file or directory to analyze")
@click.option("--config", "-c", 
              help="Path to configuration YAML file")
@click.option("--deviations", "-d", 
              help="Path to deviations YAML file")
@click.option("--output", "-o", 
              help="Output file path (default: stdout)")
@click.option("--standard", "-s", multiple=True,
              type=click.Choice(['MISRA', 'CERT']),
              help="Coding standards to check (can be used multiple times)")
@click.option("--rules", "-r", 
              help="Comma-separated list of specific rule IDs to run")
@click.option("--exclude-rules", 
              help="Comma-separated list of rule IDs to exclude")
@click.option("--format", "-f", 
              type=click.Choice(['json', 'yaml', 'text']),
              default='json',
              help="Output format")
@click.option("--ai-explain", is_flag=True,
              help="Enable AI explanations (requires API key)")
@click.option("--fail-on-violations", is_flag=True,
              help="Exit with non-zero code if violations found")
@click.option("--fail-on-new", is_flag=True,
              help="Exit with non-zero code only on new violations (requires baseline)")
@click.option("--baseline", 
              help="Path to baseline file for comparison")
@click.option("--recursive", is_flag=True, default=True,
              help="Recursively analyze directories")
@click.option("--include-paths", "-I", multiple=True,
              help="Additional include directories")
@click.option("--verbose", "-v", is_flag=True,
              help="Enable verbose output")
def analyze(path: str,
           config: Optional[str],
           deviations: Optional[str],
           output: Optional[str],
           standard: tuple,
           rules: Optional[str],
           exclude_rules: Optional[str],
           format: str,
           ai_explain: bool,
           fail_on_violations: bool,
           fail_on_new: bool,
           baseline: Optional[str],
           recursive: bool,
           include_paths: tuple,
           verbose: bool) -> None:
    """Analyze C/C++ source code for MISRA and CERT violations."""
    
    try:
        # Load or create analyzer configuration
        if config:
            analyzer = create_analyzer_from_config_file(config, deviations)
        else:
            analyzer = create_default_analyzer()
            
            # Override config with command line options
            if standard:
                analyzer.config.config["standards"] = list(standard)
            if ai_explain:
                analyzer.config.config["ai_assistant"]["enabled"] = True
            if include_paths:
                analyzer.config.config["analysis"]["include_paths"] = list(include_paths)
        
        # Validate configuration
        if verbose:
            config_issues = analyzer.validate_config()
            if config_issues:
                click.echo("Configuration issues:", err=True)
                for issue in config_issues:
                    click.echo(f"  - {issue}", err=True)
        
        # Determine which rules to run
        enabled_rules = None
        if rules:
            enabled_rules = [rule.strip() for rule in rules.split(',')]
        
        # Determine files to analyze
        source_path = Path(path)
        if not source_path.exists():
            click.echo(f"Error: Path not found: {path}", err=True)
            sys.exit(1)
        
        # Run analysis
        if verbose:
            click.echo(f"Analyzing: {path}")
            if enabled_rules:
                click.echo(f"Rules: {', '.join(enabled_rules)}")
        
        if source_path.is_file():
            report = analyzer.analyze_files([str(source_path)], enabled_rules)
        else:
            report = analyzer.analyze_directory(str(source_path), recursive, enabled_rules)
        
        # Filter out excluded rules
        if exclude_rules:
            excluded_rule_ids = set(rule.strip() for rule in exclude_rules.split(','))
            report.violations = [v for v in report.violations 
                               if v.rule_id not in excluded_rule_ids]
        
        # Handle baseline comparison
        if fail_on_new and baseline:
            new_violations = _compare_with_baseline(report, baseline)
            if verbose:
                click.echo(f"New violations: {len(new_violations)}")
            
            # Output only new violations
            report.violations = new_violations
        
        # Generate and output report
        _output_report(report, output, format, verbose)
        
        # Exit with appropriate code
        violation_count = len(report.violations)
        if fail_on_violations and violation_count > 0:
            sys.exit(1)
        elif fail_on_new and violation_count > 0:
            sys.exit(1)
        
        if verbose:
            click.echo(f"Analysis complete. {violation_count} violations found.")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option("--output", "-o", default="static_analyzer_config.yaml",
              help="Output configuration file path")
def init_config(output: str) -> None:
    """Create a default configuration file."""
    try:
        create_default_config_file(output)
        click.echo(f"Created configuration file: {output}")
        
        # Also create sample deviations file
        deviation_file = output.replace('.yaml', '_deviations.yaml')
        deviation_manager = DeviationManager()
        deviation_manager.create_sample_deviations_file(deviation_file)
        click.echo(f"Created sample deviations file: {deviation_file}")
        
    except Exception as e:
        click.echo(f"Error creating configuration: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def list_rules() -> None:
    """List all available rules."""
    try:
        analyzer = create_default_analyzer()
        rules = analyzer.get_available_rules()
        
        # Group by standard
        misra_rules = [r for r in rules if r['standard'] == 'MISRA']
        cert_rules = [r for r in rules if r['standard'] == 'CERT']
        
        if misra_rules:
            click.echo("MISRA C:2012 Rules:")
            click.echo("=" * 20)
            for rule in sorted(misra_rules, key=lambda x: x['id']):
                click.echo(f"  {rule['id']}: {rule['title']} [{rule['severity']}]")
            click.echo()
        
        if cert_rules:
            click.echo("CERT C/C++ Rules:")
            click.echo("=" * 20)
            for rule in sorted(cert_rules, key=lambda x: x['id']):
                click.echo(f"  {rule['id']}: {rule['title']} [{rule['severity']}]")
        
    except Exception as e:
        click.echo(f"Error listing rules: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--config", "-c", 
              help="Path to configuration file to validate")
def validate_config(config: Optional[str]) -> None:
    """Validate configuration file."""
    try:
        if config:
            analyzer = create_analyzer_from_config_file(config)
        else:
            analyzer = create_default_analyzer()
        
        issues = analyzer.validate_config()
        
        if not issues:
            click.echo("✅ Configuration is valid")
        else:
            click.echo("❌ Configuration issues found:")
            for issue in issues:
                click.echo(f"  - {issue}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error validating configuration: {str(e)}", err=True)
        sys.exit(1)


def _output_report(report, output_path: Optional[str], format: str, verbose: bool) -> None:
    """Output the analysis report."""
    if format == 'json':
        content = report.to_json()
    elif format == 'yaml':
        import yaml
        content = yaml.dump(report.to_dict(), default_flow_style=False, indent=2)
    else:  # text format
        content = _format_text_report(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        if verbose:
            click.echo(f"Report written to: {output_path}")
    else:
        click.echo(content)


def _format_text_report(report) -> str:
    """Format report as human-readable text."""
    lines = []
    lines.append("Static Analysis Report")
    lines.append("=" * 50)
    lines.append(f"Total violations: {len(report.violations)}")
    lines.append("")
    
    if report.violations:
        # Group by file
        violations_by_file = {}
        for violation in report.violations:
            file_path = violation.location.file_path
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)
        
        for file_path, file_violations in violations_by_file.items():
            lines.append(f"File: {file_path}")
            lines.append("-" * len(f"File: {file_path}"))
            
            for violation in file_violations:
                lines.append(f"  {violation.location.line}:{violation.location.column} "
                           f"[{violation.severity.value}] {violation.rule_id}")
                lines.append(f"    {violation.message}")
                
                if violation.ai_explanation:
                    lines.append(f"    💡 {violation.ai_explanation}")
                
                lines.append("")
    
    return "\n".join(lines)


def _compare_with_baseline(report, baseline_path: str) -> List:
    """Compare report with baseline to find new violations."""
    try:
        import json
        with open(baseline_path, 'r', encoding='utf-8') as f:
            baseline_data = json.load(f)
        
        baseline_violations = set()
        for violation_data in baseline_data.get('violations', []):
            # Create signature for comparison
            signature = (
                violation_data['rule_id'],
                violation_data['location']['file_path'],
                violation_data['location']['line'],
                violation_data['location']['column']
            )
            baseline_violations.add(signature)
        
        # Find new violations
        new_violations = []
        for violation in report.violations:
            signature = (
                violation.rule_id,
                violation.location.file_path,
                violation.location.line,
                violation.location.column
            )
            if signature not in baseline_violations:
                new_violations.append(violation)
        
        return new_violations
        
    except Exception as e:
        click.echo(f"Warning: Could not compare with baseline: {str(e)}", err=True)
        return report.violations


def main() -> None:
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
