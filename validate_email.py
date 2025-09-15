import re
import asyncio
import aiodns
from tqdm.asyncio import tqdm

def regex_validate(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

async def network_validate(email):
    try:
        domain = email.split('@')[1]
        resolver = aiodns.DNSResolver()
        mx_records = await resolver.query(domain, 'MX')
        return len(mx_records) > 0
    except:
        return False

async def validate_email(email):
    if not regex_validate(email):
        return email, False, "Invalid format"
    
    if not await network_validate(email):
        return email, False, "No MX records"
    
    return email, True, "Valid"

async def validate_emails_parallel(emails, max_concurrent=100):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def validate_with_limit(email):
        async with semaphore:
            result = await validate_email(email)
            pbar.update(1)
            return result
    
    pbar = tqdm(total=len(emails), desc="Validating emails")
    tasks = [validate_with_limit(email) for email in emails]
    results = await asyncio.gather(*tasks)
    pbar.close()
    
    return results

def print_stats(results):
    total = len(results)
    valid = sum(1 for _, is_valid, _ in results if is_valid)
    invalid = total - valid
    
    success_rate = (valid / total * 100) if total > 0 else 0
    
    print(f"\nValidation Results:")
    print(f"Total emails: {total}")
    print(f"Valid emails: {valid}")
    print(f"Invalid emails: {invalid}")
    print(f"Success rate: {success_rate:.1f}%")
    
    failed_emails = [(email, reason) for email, is_valid, reason in results if not is_valid]
    
    if failed_emails:
        print(f"\nFailed emails ({len(failed_emails)}):")
        for email, reason in failed_emails:
            print(f"  {email}: {reason}")

if __name__ == "__main__":
    emails = []
    results = asyncio.run(validate_emails_parallel(emails, 100))
    print_stats(results)