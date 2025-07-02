"""Identity command - DID management (CSF §8)"""

import click
from cs.utils.output import success, error, info, warning
from cs.config import CSFConfig
from cs.identity import IdentityManager

@click.group()
@click.pass_context
def identity_command(ctx):
    """DID management (create, status, rotate, revoke) (CSF §8)"""
    pass

@identity_command.command()
@click.pass_context
def create(ctx):
    """Create new DID identity"""
    
    output_json = ctx.obj.get('output_json', False)
    config = ctx.obj['config']
    identity_manager = IdentityManager(config)
    
    if identity_manager.has_identity():
        existing_did = identity_manager.get_did()
        warning(f"Identity already exists: {existing_did}", output_json)
        info("Use 'cs id rotate' to create a new key", output_json)
        return
    
    try:
        info("Creating new DID identity...", output_json)
        did = identity_manager.create_identity()
        success(f"Created DID identity: {did}", output_json)
        info(f"Key stored in: {identity_manager.key_file}", output_json)
        
    except Exception as e:
        error(f"Failed to create identity: {str(e)}", output_json, exit_code=1)

@identity_command.command()
@click.pass_context  
def status(ctx):
    """Show identity status"""
    
    output_json = ctx.obj.get('output_json', False)
    config = ctx.obj['config']
    identity_manager = IdentityManager(config)
    
    status_info = identity_manager.get_identity_status()
    
    if output_json:
        import json
        print(json.dumps(status_info, indent=2))
    else:
        if status_info['status'] == 'no_identity':
            warning("No DID identity found", output_json)
            info("Run 'cs id create' to create one", output_json)
        elif status_info['status'] == 'active':
            success("DID Identity Status:", output_json)
            info(f"  DID: {status_info['did']}", output_json)
            info(f"  Created: {status_info['created']}", output_json)
            info(f"  Key Type: {status_info['key_type']}", output_json)
            info(f"  Key File: {status_info['key_file']}", output_json)
        else:
            error(f"Identity error: {status_info.get('error', 'Unknown')}", output_json)

@identity_command.command()
@click.pass_context
def rotate(ctx):
    """Rotate DID key"""
    
    output_json = ctx.obj.get('output_json', False)
    config = ctx.obj['config']
    identity_manager = IdentityManager(config)
    
    if not identity_manager.has_identity():
        error("No identity to rotate. Run 'cs id create' first.", output_json, exit_code=68)
        return
    
    try:
        old_did = identity_manager.get_did()
        info(f"Rotating key for: {old_did}", output_json)
        
        new_did = identity_manager.rotate_key()
        
        success(f"Key rotated successfully", output_json)
        info(f"Old DID: {old_did}", output_json)
        info(f"New DID: {new_did}", output_json)
        warning("Old key has been revoked", output_json)
        
    except Exception as e:
        error(f"Failed to rotate key: {str(e)}", output_json, exit_code=67)

@identity_command.command()
@click.pass_context
def revoke(ctx):
    """Revoke current DID key"""
    
    output_json = ctx.obj.get('output_json', False)
    config = ctx.obj['config']
    identity_manager = IdentityManager(config)
    
    if not identity_manager.has_identity():
        error("No identity to revoke", output_json, exit_code=68)
        return
    
    current_did = identity_manager.get_did()
    
    # Confirm revocation
    if not output_json:
        import sys
        response = input(f"Are you sure you want to revoke {current_did}? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            info("Revocation cancelled", output_json)
            return
    
    try:
        # Create revocation attestation
        revocation = {
            "attester_did": current_did,
            "timestamp": identity_manager._current_timestamp(),
            "attestation_class": "KEY_REVOCATION",
            "body": {
                "revoked_did": current_did,
                "reason": "manual_revocation"
            }
        }
        
        # Sign revocation
        signed_revocation = identity_manager.sign_attestation(revocation)
        
        # Save revocation notice
        revocation_file = identity_manager.identity_dir / f"revocation_{current_did.split(':')[-1][:8]}.json"
        import json
        with open(revocation_file, 'w') as f:
            json.dump(signed_revocation, f, indent=2)
        
        # Remove key files
        identity_manager.key_file.unlink(missing_ok=True)
        identity_manager.did_file.unlink(missing_ok=True)
        
        success(f"DID revoked: {current_did}", output_json)
        info(f"Revocation notice saved: {revocation_file}", output_json)
        warning("You will need to create a new identity with 'cs id create'", output_json)
        
    except Exception as e:
        error(f"Failed to revoke identity: {str(e)}", output_json, exit_code=67)
