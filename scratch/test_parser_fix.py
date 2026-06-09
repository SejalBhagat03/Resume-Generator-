from resume_builder.parser.engine import parse_contact_details, parse_projects

# Test contact parsing with the format from the screenshot
header = "SEJAL BHAGAT\nSEJAL BHAGAT Nagpur, India  | +91 9002644273 | bhagatsejal08@gmail.com | linkedin/Sejal.Bhagat | github/SejalBhagat03"

contacts = parse_contact_details(header)
print("Name:", contacts["name"])
print("Email:", contacts["email"])
print("Phone:", contacts["phone"])
print("LinkedIn display:", contacts["linkedin"]["display"])
print("LinkedIn url:", contacts["linkedin"]["url"])
print("GitHub display:", contacts["github"]["display"])
print("GitHub url:", contacts["github"]["url"])

print()
# Test project parsing with '| GitHub' pattern
proj_lines = [
    "Blockchain-Based Digital License & Registration System | GitHub         Jul 2025",
    "Technologies: Node.js, React, Express.js, Solidity, Hardhat, Ethers.js, IPFS, PostgreSQL",
    "o Built a blockchain-based licensing system using React, Node.js, and smart contracts",
    "o Integrated frontend, backend, and blockchain components for secure verification",
    "Labor Management System | GitHub",
    "Technologies: React, Node.js, MongoDB, REST APIs",
    "o Created a high-impact full stack system with AI-assisted record management",
]

projects = parse_projects(proj_lines)
for p in projects:
    print(f"Project: title=[{p['title']}] link={p['link']} date={p['date']}")
    print(f"         tools={p['tools']}")
    for b in p["bullets"][:1]:
        print(f"  bullet: {b[:70]}")
