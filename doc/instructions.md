

--------------------

email:

-------------------


Hi Team,

Can you please share Ollama URL access so that I want to share this with the organization. **@Alberto Hernandez** -
 Build a python interface to access . This interface should take care of
 user management so that we can create credential for an individual.

This has to be deployed on Cloud Run and please set the usage limit to control the cost.

Thanks,

Lakshman

-----------------------

DevOps answer:

---



Hi Team,

Ollama
 is currently running on a private node inside Kubernetes for security
reasons. Please confirm whether we already have a workflow or frontend
in place to restrict unauthenticated access. Otherwise, the service
could be scanned or misused.

In
 the meantime, I have added Kubernetes policies that still need to be
properly configured and enforced for any potential user consuming
Ollama. I'm attaching doc

Regards,

Raul
